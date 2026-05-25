from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BaseProductsView,
    BaseStockViewSet,
    CurrentUserView,
    DepartmentValuesView,
    DepartmentViewSet,
    DepartmentStockViewSet,
    ManagersCatalogView,
    ManagersView,
    MissingProductsView,
    MonthlyReportView,
    ProductAvailabilityView,
    ProductViewSet,
    PurchaseOrderViewSet,
    SaleViewSet,
    StoreProductsView,
    StoreViewSet,
    SupplierBaseViewSet,
    index_page,
)

router = DefaultRouter()
router.register("stores", StoreViewSet)
router.register("departments", DepartmentViewSet)
router.register("products", ProductViewSet)
router.register("supplier-bases", SupplierBaseViewSet)
router.register("base-stocks", BaseStockViewSet)
router.register("department-stocks", DepartmentStockViewSet)
router.register("purchase-orders", PurchaseOrderViewSet)
router.register("sales", SaleViewSet)

urlpatterns = [
    path("", index_page, name="index"),
    path("api/", include(router.urls)),
    path("api/me/", CurrentUserView.as_view(), name="api-me"),
    path("api/managers-catalog/", ManagersCatalogView.as_view(), name="api-managers-catalog"),
    path("api/dashboard/store-products/", StoreProductsView.as_view(), name="api-store-products"),
    path("api/dashboard/base-products/", BaseProductsView.as_view(), name="api-base-products"),
    path("api/dashboard/missing-products/", MissingProductsView.as_view(), name="api-missing-products"),
    path("api/dashboard/department-values/", DepartmentValuesView.as_view(), name="api-department-values"),
    path("api/dashboard/managers/", ManagersView.as_view(), name="api-managers"),
    path("api/dashboard/product-bases/", ProductAvailabilityView.as_view(), name="api-product-bases"),
    path("api/reports/monthly/", MonthlyReportView.as_view(), name="api-monthly-report"),
    path("api-auth/", include("rest_framework.urls")),
]

