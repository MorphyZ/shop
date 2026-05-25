from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

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
from .services import apply_sale_inventory, receive_purchase_order


class InventoryFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="admin", password="admin12345")

        self.store = Store.objects.create(name="Test Store", number="100", store_class=Store.StoreClass.STANDARD)
        self.department = Department.objects.create(store=self.store, name="Бакалея", manager=self.user)
        self.base = SupplierBase.objects.create(name="Base 1", city="EKB")
        self.product = Product.objects.create(name="Сахар", unit=Product.Unit.KILOGRAM, preferred_base=self.base)

        self.base_stock = BaseStock.objects.create(
            base=self.base,
            product=self.product,
            grade="Первый",
            quantity=100,
            purchase_price=Decimal("50.00"),
        )

    def test_receive_purchase_updates_base_and_department_stock(self):
        order = PurchaseOrder.objects.create(
            store=self.store,
            supplier_base=self.base,
            department=self.department,
            created_by=self.user,
            status=PurchaseOrder.Status.DRAFT,
        )
        PurchaseOrderItem.objects.create(
            order=order,
            product=self.product,
            grade="Первый",
            quantity=10,
            purchase_price=Decimal("50.00"),
        )

        receive_purchase_order(order)

        self.base_stock.refresh_from_db()
        self.assertEqual(self.base_stock.quantity, 90)

        department_stock = DepartmentStock.objects.get(
            department=self.department,
            product=self.product,
            grade="Первый",
        )
        self.assertEqual(department_stock.quantity, 10)

        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.RECEIVED)

    def test_sale_decreases_department_stock(self):
        DepartmentStock.objects.create(
            department=self.department,
            product=self.product,
            grade="Первый",
            quantity=20,
            retail_price=Decimal("65.00"),
        )

        sale = Sale.objects.create(store=self.store, department=self.department, sold_by=self.user)
        SaleItem.objects.create(
            sale=sale,
            product=self.product,
            grade="Первый",
            quantity=5,
            retail_price=Decimal("65.00"),
        )

        apply_sale_inventory(sale)

        stock = DepartmentStock.objects.get(department=self.department, product=self.product, grade="Первый")
        self.assertEqual(stock.quantity, 15)
