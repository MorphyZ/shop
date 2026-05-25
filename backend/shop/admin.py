from django.contrib import admin

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


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "number", "store_class")
    search_fields = ("name", "number")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "store", "manager", "is_open")
    list_filter = ("store", "is_open")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "preferred_base")
    search_fields = ("name",)


@admin.register(SupplierBase)
class SupplierBaseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "contact_phone")
    search_fields = ("name", "city")


@admin.register(BaseStock)
class BaseStockAdmin(admin.ModelAdmin):
    list_display = ("id", "base", "product", "grade", "quantity", "purchase_price")
    list_filter = ("base", "product")


@admin.register(DepartmentStock)
class DepartmentStockAdmin(admin.ModelAdmin):
    list_display = ("id", "department", "product", "grade", "quantity", "retail_price")
    list_filter = ("department", "product")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "supplier_base", "department", "status", "created_at")
    list_filter = ("status", "store", "supplier_base")
    inlines = [PurchaseOrderItemInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "department", "sold_by", "sold_at")
    list_filter = ("store", "department")
    inlines = [SaleItemInline]


admin.site.register(PurchaseOrderItem)
admin.site.register(SaleItem)

