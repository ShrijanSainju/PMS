from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import UserProfile, Vehicle, Booking
from django.utils import timezone
from datetime import timedelta
import re


class EnhancedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPES, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes and placeholders
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter phone number (optional)'
        })
        self.fields['user_type'].widget.attrs.update({
            'class': 'form-control'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid phone number.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.user_type = self.cleaned_data['user_type']
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.save()

        return user


class EnhancedAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remember_me'].widget.attrs.update({
            'class': 'form-check-input'
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow login with email or username
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No user found with this email address.")
        return email


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'date_of_birth', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }


class VehicleEntryForm(forms.Form):
    vehicle_number = forms.CharField(
        label="Vehicle Number",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter vehicle number (e.g., ABC-1234)',
            'style': 'text-transform: uppercase;'
        })
    )

    def clean_vehicle_number(self):
        vehicle_number = self.cleaned_data.get('vehicle_number')
        if vehicle_number:
            vehicle_number = vehicle_number.upper().strip()
            # Basic validation for vehicle number format
            if not re.match(r'^[A-Z0-9\-\s]+$', vehicle_number):
                raise ValidationError("Vehicle number can only contain letters, numbers, hyphens, and spaces.")
        return vehicle_number


class LookupForm(forms.Form):
    vehicle_number = forms.CharField(
        label="Enter Your Vehicle Number",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your vehicle number',
            'style': 'text-transform: uppercase;'
        })
    )

    def clean_vehicle_number(self):
        vehicle_number = self.cleaned_data.get('vehicle_number')
        if vehicle_number:
            vehicle_number = vehicle_number.upper().strip()
        return vehicle_number


# Legacy forms for backward compatibility with customer, staff, and manager apps
class CustomerRegisterForm(UserCreationForm):
    """Legacy form for customer registration - redirects to enhanced form"""
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Create user profile with customer type
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.user_type = 'customer'
            profile.save()

        return user


class StaffRegisterForm(UserCreationForm):
    """Legacy form for staff registration - redirects to enhanced form"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = True
        user.is_active = False  # Inactive until approved

        if commit:
            user.save()
            # Create/update user profile with staff type and pending status
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.user_type = 'staff'
            profile.approval_status = 'pending'  # Require approval
            profile.save()

        return user


class VehicleForm(forms.ModelForm):
    """Form for customers to add/edit their vehicles"""

    class Meta:
        model = Vehicle
        fields = ['plate_number', 'vehicle_type', 'make', 'model', 'year', 'color']
        widgets = {
            'plate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ABC-1234',
                'style': 'text-transform: uppercase;'
            }),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Toyota, Honda'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Camry, Civic'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2020',
                'min': '1900',
                'max': '2030'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Red, Blue'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make plate_number required and add validation
        self.fields['plate_number'].required = True

        # Add help text
        self.fields['plate_number'].help_text = "Enter your vehicle's license plate number"
        self.fields['vehicle_type'].help_text = "Select your vehicle type"
        self.fields['make'].help_text = "Vehicle manufacturer (optional)"
        self.fields['model'].help_text = "Vehicle model (optional)"
        self.fields['year'].help_text = "Manufacturing year (optional)"
        self.fields['color'].help_text = "Vehicle color (optional)"

    def clean_plate_number(self):
        """Validate and format plate number"""
        plate_number = self.cleaned_data.get('plate_number', '').upper().strip()

        if not plate_number:
            raise ValidationError("Plate number is required.")

        # Basic validation - adjust regex based on your country's plate format
        if not re.match(r'^[A-Z0-9\-\s]{3,15}$', plate_number):
            raise ValidationError("Please enter a valid plate number (3-15 characters, letters, numbers, hyphens, and spaces only).")

        # Check if plate number already exists (excluding current instance)
        existing_vehicle = Vehicle.objects.filter(plate_number=plate_number)
        if self.instance.pk:
            existing_vehicle = existing_vehicle.exclude(pk=self.instance.pk)

        if existing_vehicle.exists():
            raise ValidationError("A vehicle with this plate number is already registered.")

        return plate_number

    def clean_year(self):
        """Validate vehicle year"""
        year = self.cleaned_data.get('year')
        if year:
            current_year = timezone.now().year
            if year < 1900 or year > current_year + 1:
                raise ValidationError(f"Please enter a valid year between 1900 and {current_year + 1}.")
        return year


class BookingForm(forms.ModelForm):
    """Form for customers to create parking bookings"""
    
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        help_text="Select which vehicle you'll be parking"
    )
    
    scheduled_arrival = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'required': True
        }),
        help_text="When do you plan to arrive?"
    )
    
    expected_duration = forms.IntegerField(
        min_value=30,
        max_value=1440,  # 24 hours max
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 120',
            'min': '30',
            'step': '30',
            'required': True
        }),
        help_text="How long will you stay? (in minutes, minimum 30)"
    )
    
    # Keep slot as a regular field, not a model field
    slot = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'selectedSlotInput'}),
        required=True,
        error_messages={'required': 'Please select a parking slot'}
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requests or notes (optional)'
        }),
        help_text="Optional: Add any special requests"
    )

    class Meta:
        model = Booking
        fields = ['vehicle', 'scheduled_arrival', 'expected_duration', 'notes']
        # Exclude 'slot' - it's defined as a regular field above and handled manually

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter vehicles to only show user's active vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            owner=user,
            is_active=True
        )
        self.user = user

    def clean_scheduled_arrival(self):
        """Validate scheduled arrival time"""
        scheduled_arrival = self.cleaned_data.get('scheduled_arrival')
        now = timezone.now()

        # For testing: allow immediate bookings (1 hour requirement disabled)
        # Must be at least 1 hour in future
        # if scheduled_arrival <= now + timedelta(hours=1):
        #     raise ValidationError("Booking must be at least 1 hour in advance.")
        
        # Allow bookings from current time onwards
        if scheduled_arrival < now:
            raise ValidationError("Booking cannot be in the past.")

        # Cannot book more than 7 days in advance
        if scheduled_arrival > now + timedelta(days=7):
            raise ValidationError("Cannot book more than 7 days in advance.")

        return scheduled_arrival

    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        scheduled_arrival = cleaned_data.get('scheduled_arrival')

        if vehicle and scheduled_arrival:
            # Check if vehicle already has a booking for this time
            existing_booking = Booking.objects.filter(
                vehicle=vehicle,
                status__in=['pending', 'confirmed'],
                scheduled_arrival__date=scheduled_arrival.date()
            ).exists()

            if existing_booking:
                raise ValidationError(f"Vehicle {vehicle.plate_number} already has a booking for this date.")

        return cleaned_data
