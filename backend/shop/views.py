from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    BaseStock,
    Department,
    DepartmentStock,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Sale,
    SaleItem,
    Store,
    SupplierBase,
)
from .permissions import IsAdminOnly, IsAdminOrReadOnly, IsAdminOrUserCanCreateSale, is_admin
from .serializers import (
    BaseStockSerializer,
    DepartmentSerializer,
    DepartmentStockSerializer,
    ProductSerializer,
    PurchaseOrderSerializer,
    SaleSerializer,
    StoreSerializer,
    SupplierBaseSerializer,
)
from .services import build_purchase_order_pdf, receive_purchase_order


def index_page(request):
    return render(request, "index.html")


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by("id")
    serializer_class = StoreSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "number"]


class SupplierBaseViewSet(viewsets.ModelViewSet):
    queryset = SupplierBase.objects.all().order_by("id")
    serializer_class = SupplierBaseSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "city"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("preferred_base").all().order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    filterset_fields = ["unit", "preferred_base"]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("store", "manager").all().order_by("id")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "manager__username"]
    filterset_fields = ["store", "is_open"]

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def inventory(self, request, pk=None):
        department = self.get_object()
        queryset = department.stocks.select_related("product").order_by("product__name", "grade")
        serializer = DepartmentStockSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOnly])
    def close(self, request, pk=None):
        department = self.get_object()
        department.is_open = False
        department.save(update_fields=["is_open"])
        return Response({"status": "closed"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOnly])
    def open(self, request, pk=None):
        department = self.get_object()
        department.is_open = True
        department.save(update_fields=["is_open"])
        return Response({"status": "open"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOnly])
    def move_stock(self, request, pk=None):
        source_department = self.get_object()
        target_department_id = request.data.get("target_department")
        product_id = request.data.get("product")
        grade = request.data.get("grade")
        quantity = request.data.get("quantity")

        if not all([target_department_id, product_id, grade, quantity]):
            return Response(
                {"detail": "Нужны поля: target_department, product, grade, quantity."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "Количество должно быть целым числом больше 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_department = Department.objects.get(pk=target_department_id)
        except Department.DoesNotExist:
            return Response({"detail": "Отдел назначения не найден."}, status=status.HTTP_404_NOT_FOUND)

        if source_department.store_id != target_department.store_id:
            return Response(
                {"detail": "Перемещать товар можно только между отделами одного магазина."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            source_stock = (
                DepartmentStock.objects.select_for_update()
                .filter(department=source_department, product_id=product_id, grade=grade)
                .first()
            )
            if source_stock is None:
                return Response({"detail": "Исходный остаток не найден."}, status=status.HTTP_404_NOT_FOUND)
            if source_stock.quantity < quantity:
                return Response(
                    {"detail": "Недостаточно товара в исходном отделе."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            target_stock = (
                DepartmentStock.objects.select_for_update()
                .filter(department=target_department, product_id=product_id, grade=grade)
                .first()
            )

            source_stock.quantity = F("quantity") - quantity
            source_stock.save(update_fields=["quantity", "updated_at"])

            if target_stock is None:
                DepartmentStock.objects.create(
                    department=target_department,
                    product=source_stock.product,
                    grade=source_stock.grade,
                    quantity=quantity,
                    retail_price=source_stock.retail_price,
                )
            else:
                target_stock.quantity = F("quantity") + quantity
                target_stock.retail_price = source_stock.retail_price
                target_stock.save(update_fields=["quantity", "retail_price", "updated_at"])

        return Response({"status": "ok"})


class BaseStockViewSet(viewsets.ModelViewSet):
    queryset = BaseStock.objects.select_related("base", "product").all().order_by("id")
    serializer_class = BaseStockSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["product__name", "grade", "base__name"]
    filterset_fields = ["base", "product", "grade"]


class DepartmentStockViewSet(viewsets.ModelViewSet):
    queryset = DepartmentStock.objects.select_related("department", "product").all().order_by("id")
    serializer_class = DepartmentStockSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["product__name", "grade", "department__name"]
    filterset_fields = ["department", "product", "grade"]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = (
        PurchaseOrder.objects.select_related("store", "supplier_base", "department", "created_by")
        .prefetch_related("items__product")
        .all()
        .order_by("-created_at")
    )
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["store", "supplier_base", "department", "status"]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOnly])
    def receive(self, request, pk=None):
        order = self.get_object()
        try:
            receive_purchase_order(order)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def document(self, request, pk=None):
        order = self.get_object()
        pdf_bytes = build_purchase_order_pdf(order)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=purchase_order_{order.id}.pdf"
        return response


class SaleViewSet(viewsets.ModelViewSet):
    queryset = (
        Sale.objects.select_related("store", "department", "sold_by")
        .prefetch_related("items__product")
        .all()
        .order_by("-sold_at")
    )
    serializer_class = SaleSerializer
    permission_classes = [IsAdminOrUserCanCreateSale]
    filterset_fields = ["store", "department"]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = [group.name for group in request.user.groups.all()]
        if request.user.is_superuser and "admin" not in roles:
            roles.append("admin")
        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "is_admin": is_admin(request.user),
                "roles": roles,
            }
        )


class StoreProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        queryset = DepartmentStock.objects.select_related("department", "product")
        if store_id:
            queryset = queryset.filter(department__store_id=store_id)

        data = (
            queryset.values("product_id", "product__name", "grade")
            .annotate(
                total_quantity=Coalesce(Sum("quantity"), 0),
                avg_retail=Coalesce(
                    Avg("retail_price"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("product__name", "grade")
        )
        return Response(list(data))


class BaseProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        base_id = request.query_params.get("base_id")
        queryset = BaseStock.objects.select_related("base", "product")
        if base_id:
            queryset = queryset.filter(base_id=base_id)

        data = (
            queryset.values("base_id", "base__name", "product_id", "product__name", "grade")
            .annotate(
                total_quantity=Coalesce(Sum("quantity"), 0),
                min_price=Coalesce(
                    Avg("purchase_price"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("base__name", "product__name")
        )
        return Response(list(data))


class MissingProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response({"detail": "Параметр store_id обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        existing_ids = (
            DepartmentStock.objects.filter(department__store_id=store_id, quantity__gt=0)
            .values_list("product_id", flat=True)
            .distinct()
        )

        missing_products = Product.objects.exclude(id__in=existing_ids).order_by("name")
        payload = []

        for product in missing_products:
            options = BaseStock.objects.filter(product=product, quantity__gt=0).select_related("base")
            option_data = [
                {
                    "base_id": stock.base_id,
                    "base_name": stock.base.name,
                    "grade": stock.grade,
                    "quantity": stock.quantity,
                    "purchase_price": stock.purchase_price,
                }
                for stock in options
            ]

            payload.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "preferred_base_id": product.preferred_base_id,
                    "options": option_data,
                }
            )

        return Response(payload)


class DepartmentValuesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        queryset = Department.objects.select_related("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        results = []
        for department in queryset:
            total_value = (
                DepartmentStock.objects.filter(department=department).aggregate(
                    total=Coalesce(
                        Sum(F("quantity") * F("retail_price"), output_field=DecimalField(max_digits=14, decimal_places=2)),
                        Decimal("0"),
                    )
                )["total"]
                or Decimal("0")
            )
            results.append(
                {
                    "department_id": department.id,
                    "department_name": department.name,
                    "store_id": department.store_id,
                    "store_name": department.store.name,
                    "total_value": total_value,
                }
            )

        return Response(results)


class ManagersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        queryset = Department.objects.select_related("manager", "store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        data = [
            {
                "department_id": dep.id,
                "department_name": dep.name,
                "store_name": dep.store.name,
                "manager_username": dep.manager.username if dep.manager else None,
                "manager_email": dep.manager.email if dep.manager else None,
            }
            for dep in queryset.order_by("name")
        ]
        return Response(data)


class ProductAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_name = request.query_params.get("product_name")
        if not product_name:
            return Response(
                {"detail": "Параметр product_name обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stocks = BaseStock.objects.select_related("base", "product").filter(product__name__icontains=product_name)
        payload = [
            {
                "product_name": stock.product.name,
                "base_name": stock.base.name,
                "base_id": stock.base_id,
                "grade": stock.grade,
                "quantity": stock.quantity,
                "purchase_price": stock.purchase_price,
            }
            for stock in stocks.order_by("product__name", "base__name")
        ]
        return Response(payload)


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response({"detail": "Параметр store_id обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.localdate()
        year = int(request.query_params.get("year", now.year))
        month = int(request.query_params.get("month", now.month))

        start_dt = timezone.make_aware(datetime(year, month, 1, 0, 0, 0))
        if month == 12:
            end_dt = timezone.make_aware(datetime(year + 1, 1, 1, 0, 0, 0))
        else:
            end_dt = timezone.make_aware(datetime(year, month + 1, 1, 0, 0, 0))

        purchases = PurchaseOrderItem.objects.select_related(
            "order__department",
            "product",
            "order__supplier_base",
        ).filter(
            order__store_id=store_id,
            order__status=PurchaseOrder.Status.RECEIVED,
            order__updated_at__gte=start_dt,
            order__updated_at__lt=end_dt,
        )

        sales = SaleItem.objects.select_related("sale__department", "product").filter(
            sale__store_id=store_id,
            sale__sold_at__gte=start_dt,
            sale__sold_at__lt=end_dt,
        )

        grouped: dict[int, dict] = defaultdict(
            lambda: {
                "department_id": None,
                "department_name": None,
                "purchased": [],
                "sold": [],
                "purchase_total": Decimal("0"),
                "sales_total": Decimal("0"),
                "profit": Decimal("0"),
            }
        )

        for item in purchases:
            department = item.order.department
            if department is None:
                continue

            dep_data = grouped[department.id]
            dep_data["department_id"] = department.id
            dep_data["department_name"] = department.name
            cost = Decimal(item.quantity) * item.purchase_price
            dep_data["purchase_total"] += cost
            dep_data["purchased"].append(
                {
                    "product": item.product.name,
                    "grade": item.grade,
                    "quantity": item.quantity,
                    "unit_price": item.purchase_price,
                    "total": cost,
                    "supplier_base": item.order.supplier_base.name,
                }
            )

        for item in sales:
            department = item.sale.department
            dep_data = grouped[department.id]
            dep_data["department_id"] = department.id
            dep_data["department_name"] = department.name
            revenue = Decimal(item.quantity) * item.retail_price
            dep_data["sales_total"] += revenue
            dep_data["sold"].append(
                {
                    "product": item.product.name,
                    "grade": item.grade,
                    "quantity": item.quantity,
                    "unit_price": item.retail_price,
                    "total": revenue,
                }
            )

        result = []
        for dep_id, dep_data in grouped.items():
            dep_data["profit"] = dep_data["sales_total"] - dep_data["purchase_total"]
            result.append(dep_data)

        totals = {
            "purchase_total": sum((item["purchase_total"] for item in result), Decimal("0")),
            "sales_total": sum((item["sales_total"] for item in result), Decimal("0")),
        }
        totals["profit"] = totals["sales_total"] - totals["purchase_total"]

        return Response(
            {
                "store_id": int(store_id),
                "year": year,
                "month": month,
                "departments": result,
                "totals": totals,
            }
        )


class ManagersCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        User = get_user_model()
        users = User.objects.filter(is_active=True).order_by("username")
        payload = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
        return Response(payload)

