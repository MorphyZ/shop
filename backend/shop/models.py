from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q


class Store(models.Model):
    class StoreClass(models.TextChoices):
        ECONOMY = "ECONOMY", "Эконом"
        STANDARD = "STANDARD", "Стандарт"
        PREMIUM = "PREMIUM", "Премиум"

    name = models.CharField(max_length=120)
    number = models.CharField(max_length=32, unique=True)
    store_class = models.CharField(
        max_length=16,
        choices=StoreClass.choices,
        default=StoreClass.STANDARD,
    )

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"

    def __str__(self) -> str:
        return f"{self.name} (№{self.number})"

    @property
    def markup_percent(self) -> Decimal:
        mapping = {
            self.StoreClass.ECONOMY: Decimal("0.12"),
            self.StoreClass.STANDARD: Decimal("0.20"),
            self.StoreClass.PREMIUM: Decimal("0.32"),
        }
        return mapping[self.store_class]


class Department(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    is_open = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        constraints = [
            models.UniqueConstraint(fields=["store", "name"], name="uniq_department_store_name")
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.store})"


class SupplierBase(models.Model):
    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    contact_email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Торговая база"
        verbose_name_plural = "Торговые базы"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "PCS", "шт"
        KILOGRAM = "KG", "кг"
        LITER = "L", "л"
        PACK = "PACK", "упак"

    name = models.CharField(max_length=150, unique=True)
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.PIECE)
    preferred_base = models.ForeignKey(
        SupplierBase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_products",
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self) -> str:
        return self.name


class BaseStock(models.Model):
    base = models.ForeignKey(SupplierBase, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="base_stocks")
    grade = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Остаток на базе"
        verbose_name_plural = "Остатки на базах"
        constraints = [
            models.UniqueConstraint(
                fields=["base", "product", "grade"],
                name="uniq_base_product_grade",
            ),
            CheckConstraint(condition=Q(purchase_price__gt=0), name="base_purchase_price_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.base}: {self.product} ({self.grade})"


class DepartmentStock(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="department_stocks")
    grade = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField(default=0)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Остаток в отделе"
        verbose_name_plural = "Остатки в отделах"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "product", "grade"],
                name="uniq_department_product_grade",
            ),
            CheckConstraint(condition=Q(retail_price__gt=0), name="retail_price_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.department}: {self.product} ({self.grade})"


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        CONFIRMED = "CONFIRMED", "Подтвержден"
        RECEIVED = "RECEIVED", "Получен"
        CANCELLED = "CANCELLED", "Отменен"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="purchase_orders")
    supplier_base = models.ForeignKey(
        SupplierBase,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_purchase_orders",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Закупка"
        verbose_name_plural = "Закупки"

    def __str__(self) -> str:
        return f"Закупка #{self.id} ({self.supplier_base})"


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_items")
    grade = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Позиция закупки"
        verbose_name_plural = "Позиции закупки"
        constraints = [
            models.UniqueConstraint(fields=["order", "product", "grade"], name="uniq_order_product_grade"),
            CheckConstraint(condition=Q(quantity__gt=0), name="purchase_item_qty_gt_0"),
            CheckConstraint(condition=Q(purchase_price__gt=0), name="purchase_item_price_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.product} ({self.grade}) x{self.quantity}"


class Sale(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="sales")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="sales")
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )
    sold_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"

    def __str__(self) -> str:
        return f"Продажа #{self.id} ({self.department})"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    grade = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Позиция продажи"
        verbose_name_plural = "Позиции продажи"
        constraints = [
            models.UniqueConstraint(fields=["sale", "product", "grade"], name="uniq_sale_product_grade"),
            CheckConstraint(condition=Q(quantity__gt=0), name="sale_item_qty_gt_0"),
            CheckConstraint(condition=Q(retail_price__gt=0), name="sale_item_price_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.product} ({self.grade}) x{self.quantity}"


