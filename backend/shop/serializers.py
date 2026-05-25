from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

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
from .services import apply_sale_inventory


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "number", "store_class", "markup_percent"]


class SupplierBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBase
        fields = [
            "id",
            "name",
            "city",
            "address",
            "contact_phone",
            "contact_email",
        ]


class ProductSerializer(serializers.ModelSerializer):
    preferred_base_name = serializers.CharField(source="preferred_base.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "unit",
            "preferred_base",
            "preferred_base_name",
            "description",
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    manager_username = serializers.CharField(source="manager.username", read_only=True)

    class Meta:
        model = Department
        fields = ["id", "store", "name", "manager", "manager_username", "is_open"]


class BaseStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    base_name = serializers.CharField(source="base.name", read_only=True)

    class Meta:
        model = BaseStock
        fields = [
            "id",
            "base",
            "base_name",
            "product",
            "product_name",
            "grade",
            "quantity",
            "purchase_price",
        ]


class DepartmentStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = DepartmentStock
        fields = [
            "id",
            "department",
            "department_name",
            "product",
            "product_name",
            "grade",
            "quantity",
            "retail_price",
            "updated_at",
        ]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "grade",
            "quantity",
            "purchase_price",
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)
    supplier_base_name = serializers.CharField(source="supplier_base.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "store",
            "supplier_base",
            "supplier_base_name",
            "department",
            "department_name",
            "created_by",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        store = attrs.get("store") or getattr(self.instance, "store", None)
        department = attrs.get("department")
        if department is None and self.instance is not None:
            department = self.instance.department

        if store and department and department.store_id != store.id:
            raise serializers.ValidationError("Отдел должен принадлежать выбранному магазину.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        user = request.user if request else None
        order = PurchaseOrder.objects.create(created_by=user, **validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(order=order, **item_data)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(order=instance, **item_data)

        return instance


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "grade", "quantity", "retail_price"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "store",
            "department",
            "department_name",
            "sold_by",
            "sold_at",
            "notes",
            "items",
        ]
        read_only_fields = ["sold_by", "sold_at"]

    def validate(self, attrs):
        store = attrs.get("store") or getattr(self.instance, "store", None)
        department = attrs.get("department") or getattr(self.instance, "department", None)
        if store and department and department.store_id != store.id:
            raise serializers.ValidationError("Отдел должен принадлежать выбранному магазину.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        user = request.user if request else None

        sale = Sale.objects.create(sold_by=user, **validated_data)
        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)

        apply_sale_inventory(sale)
        return sale

