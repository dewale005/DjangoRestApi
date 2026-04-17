"""webapp URL Configuration"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from webapp.api import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'tenants', views.TenantViewSet)
router.register(r'partners', views.PartnerViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'categories', views.ProductCategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'stock-levels', views.StockLevelViewSet)
router.register(r'stock-movements', views.StockMovementViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'purchase-order-lines', views.PurchaseOrderLineViewSet)
router.register(r'sales-orders', views.SalesOrderViewSet)
router.register(r'sales-order-lines', views.SalesOrderLineViewSet)
router.register(r'bom', views.BillOfMaterialViewSet)
router.register(r'manufacturing-orders', views.ManufacturingOrderViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'payroll', views.PayrollEntryViewSet)
router.register(r'accounts', views.AccountViewSet)
router.register(r'journal-entries', views.JournalEntryViewSet)
router.register(r'journal-lines', views.JournalLineViewSet)
router.register(r'leads', views.LeadViewSet)
router.register(r'pos-terminals', views.PosTerminalViewSet)
router.register(r'pos-sessions', views.PosSessionViewSet)
router.register(r'pos-sales', views.PosSaleViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    url(r'^pos/sessions/open/$', views.PosSessionOpenApi.as_view(), name='pos-session-open'),
    url(r'^pos/sales/checkout/$', views.PosCheckoutApi.as_view(), name='pos-sale-checkout'),
    url(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
