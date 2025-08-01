#!/usr/bin/env python
"""
Create test parking sessions to demonstrate user-vehicle relationship display
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from pms.models import Vehicle, ParkingSession, ParkingSlot, UserProfile
from django.utils import timezone

def create_test_sessions():
    """Create test parking sessions for demonstration"""
    print("🚀 Creating test parking sessions...")
    
    # Get or create test slots
    slot_a1, _ = ParkingSlot.objects.get_or_create(slot_id='A1')
    slot_a2, _ = ParkingSlot.objects.get_or_create(slot_id='A2')
    slot_b1, _ = ParkingSlot.objects.get_or_create(slot_id='B1')
    
    # Get the existing user with vehicle
    user_with_vehicle = User.objects.filter(vehicles__isnull=False).first()
    if user_with_vehicle:
        vehicle = user_with_vehicle.vehicles.first()
        print(f"✅ Found user: {user_with_vehicle.get_full_name() or user_with_vehicle.username}")
        print(f"   Vehicle: {vehicle.plate_number}")
        
        # Create an active session for this registered user
        session, created = ParkingSession.objects.get_or_create(
            vehicle_number=vehicle.plate_number,
            slot=slot_a1,
            defaults={
                'status': 'active',
                'start_time': timezone.now()
            }
        )
        
        if created:
            slot_a1.is_occupied = True
            slot_a1.save()
            print(f"✅ Created active session for {vehicle.plate_number} in slot A1")
        else:
            print(f"ℹ️ Session already exists for {vehicle.plate_number}")
    
    # Create a session for an unregistered vehicle
    unregistered_session, created = ParkingSession.objects.get_or_create(
        vehicle_number='XYZ789',
        slot=slot_a2,
        defaults={
            'status': 'active',
            'start_time': timezone.now()
        }
    )
    
    if created:
        slot_a2.is_occupied = True
        slot_a2.save()
        print("✅ Created active session for unregistered vehicle XYZ789 in slot A2")
    else:
        print("ℹ️ Session already exists for XYZ789")
    
    # Create a pending session for another registered user (if exists)
    other_users = User.objects.filter(vehicles__isnull=False).exclude(id=user_with_vehicle.id if user_with_vehicle else None)
    if other_users.exists():
        other_user = other_users.first()
        other_vehicle = other_user.vehicles.first()
        
        pending_session, created = ParkingSession.objects.get_or_create(
            vehicle_number=other_vehicle.plate_number,
            slot=slot_b1,
            defaults={
                'status': 'pending'
            }
        )
        
        if created:
            slot_b1.is_reserved = True
            slot_b1.save()
            print(f"✅ Created pending session for {other_vehicle.plate_number} in slot B1")
        else:
            print(f"ℹ️ Session already exists for {other_vehicle.plate_number}")
    
    print("\n🎯 Test sessions created! Now you can:")
    print("1. Visit the staff dashboard to see user names in slot grids")
    print("2. Visit the manager dashboard to see enhanced slot information")
    print("3. Check the history page for detailed user information")
    print("4. Use the lookup functionality to see user details")
    print("5. Try ending sessions to see user names in dropdowns")
    
    print(f"\n🌐 Open: http://127.0.0.1:8000/auth/login/")
    print("   Use staff or manager credentials to see the improvements")

if __name__ == "__main__":
    create_test_sessions()
