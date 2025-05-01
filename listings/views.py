from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Landlord, Location, VoucherType, Property, 
    PropertyImage, Amenity, Booking
)
from .serializers import (
    LandlordSerializer, LocationSerializer, VoucherTypeSerializer,
    PropertySerializer, PropertyListSerializer, PropertyImageSerializer,
    AmenitySerializer
)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime

# Frontend Views
def index(request):
    # Get featured properties with proper ordering and filtering
    featured_properties = Property.objects.filter(
        is_available=True
    ).select_related(
        'location'
    ).prefetch_related(
        'images'
    ).order_by(
        '-rating',  # Higher rated properties first
        '-created_at'  # Then newer properties
    ).distinct()[:4]  # Get only 4 properties
    
    return render(request, 'listings/index.html', {
        'featured_properties': featured_properties
    })

def property_list(request):
    properties = Property.objects.filter(
        is_available=True
    ).select_related(
        'location'
    ).prefetch_related(
        'images',
        'property_amenities__amenity'
    )
    
    # Get all property types for the filter
    property_types = Property.PROPERTY_TYPE_CHOICES
    
    # Filter by property type
    property_type = request.GET.get('property_type')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # Filter by location
    location = request.GET.get('location')
    if location:
        properties = properties.filter(location__city__icontains=location)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        properties = properties.filter(rent_amount__gte=float(min_price))
    if max_price:
        properties = properties.filter(rent_amount__lte=float(max_price))
    
    # Filter by bedrooms
    bedrooms = request.GET.get('bedrooms')
    if bedrooms:
        properties = properties.filter(bedrooms__gte=int(bedrooms))
    
    # Filter by amenities
    amenities = request.GET.getlist('amenities')
    if amenities:
        properties = properties.filter(property_amenities__amenity__name__in=amenities)
    
    # Sort properties
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['rent_amount', '-rent_amount', 'rating', '-rating', 'created_at', '-created_at']:
        properties = properties.order_by(sort_by)
    
    # Get all available amenities for the filter sidebar
    all_amenities = Amenity.objects.all()
    
    # Get unique locations for the location filter
    locations = Location.objects.filter(property__in=properties).distinct()
    
    return render(request, 'listings/property_list.html', {
        'properties': properties,
        'property_types': property_types,
        'all_amenities': all_amenities,
        'locations': locations,
        'filters': {
            'property_type': property_type,
            'location': location,
            'min_price': min_price,
            'max_price': max_price,
            'bedrooms': bedrooms,
            'amenities': amenities,
            'sort_by': sort_by
        }
    })

def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    similar_properties = Property.objects.filter(
        location=property.location,
        is_available=True
    ).exclude(pk=property.pk)[:3]
    return render(request, 'listings/property_detail.html', {
        'property': property,
        'similar_properties': similar_properties
    })

@login_required
def my_bookings(request):
    return render(request, 'listings/my_bookings.html')

def how_it_works(request):
    return render(request, 'listings/how_it_works.html')

def testimonials(request):
    return render(request, 'listings/testimonials.html')

def contact(request):
    return render(request, 'listings/contact.html')

def about(request):
    return render(request, 'listings/about.html')

def careers(request):
    return render(request, 'listings/careers.html')

def press(request):
    return render(request, 'listings/press.html')

def blog(request):
    return render(request, 'listings/blog.html')

def faq(request):
    return render(request, 'listings/faq.html')

def privacy(request):
    return render(request, 'listings/privacy.html')

def terms(request):
    return render(request, 'listings/terms.html')

def safety(request):
    return render(request, 'listings/safety.html')

@login_required
def profile(request):
    return render(request, 'listings/profile.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'listings/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'listings/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')

def search(request):
    properties = Property.objects.filter(is_available=True)
    
    # Filter by budget
    budget = request.GET.get('budget')
    if budget == 'budget':
        properties = properties.filter(rent_amount__lte=300)
    elif budget == 'standard':
        properties = properties.filter(rent_amount__gt=300, rent_amount__lte=700)
    elif budget == 'luxury':
        properties = properties.filter(rent_amount__gt=700)
    
    # Filter by number of travelers
    travelers = request.GET.get('travelers')
    if travelers:
        if travelers == '1':
            properties = properties.filter(bedrooms__gte=1)
        elif travelers == '2':
            properties = properties.filter(bedrooms__gte=1)
        elif travelers == '3-5':
            properties = properties.filter(bedrooms__gte=2)
        elif travelers == '6+':
            properties = properties.filter(bedrooms__gte=3)
    
    # Filter by dates (if implemented)
    dates = request.GET.get('dates')
    if dates:
        # Add date filtering logic here
        pass
    
    return render(request, 'listings/property_list.html', {
        'properties': properties,
        'search_params': {
            'budget': budget,
            'travelers': travelers,
            'dates': dates
        }
    })

def book_now(request):
    return render(request, 'listings/book_now.html')

@login_required
@require_http_methods(["POST"])
def book_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    if not property.is_available:
        return JsonResponse({
            'status': 'error',
            'message': 'This property is not available for booking'
        }, status=400)
    
    try:
        # Parse dates from the request
        dates = request.POST.get('dates', '').split(' — ')
        if len(dates) != 2:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format'
            }, status=400)
            
        check_in = datetime.strptime(dates[0].strip(), '%Y-%m-%d')
        check_out = datetime.strptime(dates[1].strip(), '%Y-%m-%d')
        
        # Validate dates
        if check_in >= check_out:
            return JsonResponse({
                'status': 'error',
                'message': 'Check-out date must be after check-in date'
            }, status=400)
            
        if check_in < timezone.now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Check-in date cannot be in the past'
            }, status=400)
            
        # Get number of guests
        guests = int(request.POST.get('guests', 1))
        if guests < 1:
            return JsonResponse({
                'status': 'error',
                'message': 'Number of guests must be at least 1'
            }, status=400)
            
        # Create booking
        booking = Booking.objects.create(
            property=property,
            user=request.user,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            total_price=property.rent_amount * (check_out - check_in).days
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Booking created successfully',
            'booking_id': booking.id
        })
        
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your booking'
        }, status=500)

# API Views
class LandlordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voucher_friendly']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'country']
    search_fields = ['city', 'state', 'address']
    ordering_fields = ['city', 'state']

class VoucherTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VoucherType.objects.all()
    serializer_class = VoucherTypeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Property.objects.filter(is_available=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'property_type', 'bedrooms', 'bathrooms', 'landlord', 
        'location__city', 'location__state', 'is_featured',
        'voucher_types'
    ]
    search_fields = [
        'title', 'description', 'landlord__name', 
        'location__city', 'location__address'
    ]
    ordering_fields = ['rent_amount', 'created_at', 'rating']

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        return PropertySerializer