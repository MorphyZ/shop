from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import BaseStock, DepartmentStock, PurchaseOrder, Sale


def calculate_retail_price(purchase_price: Decimal, store_class: str) -> Decimal:
    markup_map = {
        "ECONOMY": Decimal("0.12"),
        "STANDARD": Decimal("0.20"),
        "PREMIUM": Decimal("0.32"),
    }
    markup = markup_map.get(store_class, Decimal("0.20"))
    result = purchase_price * (Decimal("1") + markup)
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def receive_purchase_order(order: PurchaseOrder) -> PurchaseOrder:
    if order.status == PurchaseOrder.Status.RECEIVED:
        raise ValidationError("Закупка уже оприходована.")

    if order.status == PurchaseOrder.Status.CANCELLED:
        raise ValidationError("Нельзя оприходовать отмененную закупку.")

    if order.department is None:
        raise ValidationError("Для оприходования укажите отдел назначения.")

    items = list(order.items.select_related("product"))
    if not items:
        raise ValidationError("Невозможно оприходовать закупку без позиций.")

    for item in items:
        base_stock = (
            BaseStock.objects.select_for_update()
            .filter(base=order.supplier_base, product=item.product, grade=item.grade)
            .first()
        )
        if base_stock is None:
            raise ValidationError(
                f"На базе {order.supplier_base.name} нет остатка: {item.product.name} ({item.grade})."
            )

        if base_stock.quantity < item.quantity:
            raise ValidationError(
                f"Недостаточно товара на базе: {item.product.name} ({item.grade})."
            )

        base_stock.quantity = F("quantity") - item.quantity
        base_stock.save(update_fields=["quantity"])

        retail_price = calculate_retail_price(item.purchase_price, order.store.store_class)
        dep_stock = (
            DepartmentStock.objects.select_for_update()
            .filter(department=order.department, product=item.product, grade=item.grade)
            .first()
        )
        if dep_stock is None:
            DepartmentStock.objects.create(
                department=order.department,
                product=item.product,
                grade=item.grade,
                quantity=item.quantity,
                retail_price=retail_price,
            )
        else:
            dep_stock.quantity = F("quantity") + item.quantity
            dep_stock.retail_price = retail_price
            dep_stock.save(update_fields=["quantity", "retail_price", "updated_at"])

    order.status = PurchaseOrder.Status.RECEIVED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def apply_sale_inventory(sale: Sale) -> Sale:
    items = list(sale.items.select_related("product"))
    if not items:
        raise ValidationError("Нельзя провести продажу без позиций.")

    for item in items:
        dep_stock = (
            DepartmentStock.objects.select_for_update()
            .filter(department=sale.department, product=item.product, grade=item.grade)
            .first()
        )
        if dep_stock is None:
            raise ValidationError(
                f"В отделе нет товара: {item.product.name} ({item.grade})."
            )

        if dep_stock.quantity < item.quantity:
            raise ValidationError(
                f"Недостаточно товара в отделе: {item.product.name} ({item.grade})."
            )

        dep_stock.quantity = F("quantity") - item.quantity
        dep_stock.save(update_fields=["quantity", "updated_at"])

    return sale


def build_purchase_order_pdf(order: PurchaseOrder) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 20 * mm
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(20 * mm, y, "Заявка на закупку товара")

    y -= 10 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, y, f"Заявка №{order.id}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"Магазин: {order.store.name} (№{order.store.number})")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"База: {order.supplier_base.name}")
    y -= 6 * mm
    department_name = order.department.name if order.department else "не указан"
    pdf.drawString(20 * mm, y, f"Отдел назначения: {department_name}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y, "Товар")
    pdf.drawString(85 * mm, y, "Сорт")
    pdf.drawString(120 * mm, y, "Кол-во")
    pdf.drawString(145 * mm, y, "Закуп. цена")

    total = Decimal("0")
    pdf.setFont("Helvetica", 10)
    for item in order.items.select_related("product").all():
        y -= 6 * mm
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica", 10)

        line_total = Decimal(item.quantity) * item.purchase_price
        total += line_total
        pdf.drawString(20 * mm, y, item.product.name[:28])
        pdf.drawString(85 * mm, y, item.grade[:20])
        pdf.drawRightString(136 * mm, y, str(item.quantity))
        pdf.drawRightString(190 * mm, y, f"{item.purchase_price} руб.")

    y -= 10 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(190 * mm, y, f"Итого: {total.quantize(Decimal('0.01'))} руб.")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()

