from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LandlordViewSet, LocationViewSet, VoucherTypeViewSet,
    PropertyViewSet, AmenityViewSet,
    # Frontend views
    index, property_list, property_detail, my_bookings,
    how_it_works, testimonials, contact, about, careers,
    press, blog, faq, privacy, terms, safety, profile,
    login, register, logout, search, book_now, book_property
)

router = DefaultRouter()
router.register(r'landlords', LandlordViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'voucher-types', VoucherTypeViewSet)
router.register(r'properties', PropertyViewSet)
router.register(r'amenities', AmenityViewSet)

urlpatterns = [
    # Frontend URLs
    path('', index, name='index'),
    path('properties/', property_list, name='property_list'),
    path('properties/<int:pk>/', property_detail, name='property_detail'),
    path('my-bookings/', my_bookings, name='my_bookings'),
    path('how-it-works/', how_it_works, name='how_it_works'),
    path('testimonials/', testimonials, name='testimonials'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('careers/', careers, name='careers'),
    path('press/', press, name='press'),
    path('blog/', blog, name='blog'),
    path('faq/', faq, name='faq'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('safety/', safety, name='safety'),
    path('profile/', profile, name='profile'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('search/', search, name='search'),
    path('book-now/', book_now, name='book_now'),
    path('properties/<int:pk>/book/', book_property, name='book_property'),
]

# API URLs
api_urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = urlpatterns + api_urlpatterns