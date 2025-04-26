from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LandlordViewSet, LocationViewSet, VoucherTypeViewSet,
    PropertyViewSet, AmenityViewSet
)

router = DefaultRouter()
router.register(r'landlords', LandlordViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'voucher-types', VoucherTypeViewSet)
router.register(r'properties', PropertyViewSet)
router.register(r'amenities', AmenityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]