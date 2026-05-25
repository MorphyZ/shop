from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from shop.models import BaseStock, Department, DepartmentStock, Product, Store, SupplierBase
from shop.services import calculate_retail_price


class Command(BaseCommand):
    help = "Создает тестовые данные для АСУ Магазин"

    def handle(self, *args, **options):
        User = get_user_model()

        admin_group, _ = Group.objects.get_or_create(name="admin")
        user_group, _ = Group.objects.get_or_create(name="user")

        admin_user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        if created:
            admin_user.set_password("admin12345")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
        admin_user.groups.add(admin_group)

        simple_user, created = User.objects.get_or_create(username="operator", defaults={"email": "user@example.com"})
        if created:
            simple_user.set_password("user12345")
            simple_user.save()
        simple_user.groups.add(user_group)

        store, _ = Store.objects.get_or_create(
            number="001",
            defaults={"name": "Продукты у дома", "store_class": Store.StoreClass.STANDARD},
        )

        dairy_department, _ = Department.objects.get_or_create(
            store=store,
            name="Молочный отдел",
            defaults={"manager": admin_user},
        )
        bakery_department, _ = Department.objects.get_or_create(
            store=store,
            name="Бакалея",
            defaults={"manager": simple_user},
        )

        base_north, _ = SupplierBase.objects.get_or_create(
            name="Северная база",
            defaults={"city": "Екатеринбург", "address": "ул. Складская, 1"},
        )
        base_south, _ = SupplierBase.objects.get_or_create(
            name="Южная база",
            defaults={"city": "Челябинск", "address": "пр. Логистики, 7"},
        )

        milk, _ = Product.objects.get_or_create(name="Молоко", defaults={"unit": Product.Unit.LITER, "preferred_base": base_north})
        bread, _ = Product.objects.get_or_create(name="Хлеб", defaults={"unit": Product.Unit.PIECE, "preferred_base": base_south})
        sugar, _ = Product.objects.get_or_create(name="Сахар", defaults={"unit": Product.Unit.KILOGRAM, "preferred_base": base_north})

        for base, product, grade, quantity, price in [
            (base_north, milk, "Высший", 250, Decimal("58.00")),
            (base_north, sugar, "Первый", 400, Decimal("52.00")),
            (base_south, bread, "Первый", 300, Decimal("32.00")),
            (base_south, milk, "Первый", 120, Decimal("55.00")),
        ]:
            BaseStock.objects.update_or_create(
                base=base,
                product=product,
                grade=grade,
                defaults={"quantity": quantity, "purchase_price": price},
            )

        for dep, product, grade, quantity, purchase_price in [
            (dairy_department, milk, "Высший", 80, Decimal("58.00")),
            (bakery_department, bread, "Первый", 90, Decimal("32.00")),
            (bakery_department, sugar, "Первый", 40, Decimal("52.00")),
        ]:
            DepartmentStock.objects.update_or_create(
                department=dep,
                product=product,
                grade=grade,
                defaults={
                    "quantity": quantity,
                    "retail_price": calculate_retail_price(purchase_price, store.store_class),
                },
            )

        self.stdout.write(self.style.SUCCESS("Демо-данные готовы."))
        self.stdout.write("admin/admin12345, operator/user12345")

