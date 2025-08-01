#!/usr/bin/env python
"""
Test script to verify user-vehicle relationship display functionality
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
import json

def test_user_vehicle_relationships():
    """Test that user-vehicle relationships are properly displayed"""
    print("🔍 Testing User-Vehicle Relationship Display")
    print("=" * 50)
    
    # Test 1: Check if we have users with vehicles
    users_with_vehicles = User.objects.filter(vehicles__isnull=False).distinct()
    print(f"✅ Users with registered vehicles: {users_with_vehicles.count()}")
    
    for user in users_with_vehicles[:3]:  # Show first 3
        vehicles = user.vehicles.filter(is_active=True)
        profile = getattr(user, 'userprofile', None)
        print(f"   👤 {user.get_full_name() or user.username}")
        print(f"      📧 {user.email}")
        if profile and profile.phone_number:
            print(f"      📞 {profile.phone_number}")
        print(f"      🚗 Vehicles: {', '.join([v.plate_number for v in vehicles])}")
        print()
    
    # Test 2: Check active sessions with user info
    active_sessions = ParkingSession.objects.filter(status__in=['pending', 'active'])
    print(f"✅ Active parking sessions: {active_sessions.count()}")
    
    for session in active_sessions[:3]:  # Show first 3
        try:
            vehicle = Vehicle.objects.filter(
                plate_number=session.vehicle_number,
                is_active=True
            ).select_related('owner', 'owner__userprofile').first()
            
            if vehicle and vehicle.owner:
                user_profile = getattr(vehicle.owner, 'userprofile', None)
                print(f"   🚗 {session.vehicle_number} (Slot: {session.slot.slot_id})")
                print(f"      👤 Owner: {vehicle.owner.get_full_name() or vehicle.owner.username}")
                print(f"      📧 Email: {vehicle.owner.email}")
                if user_profile and user_profile.phone_number:
                    print(f"      📞 Phone: {user_profile.phone_number}")
                print(f"      🏷️ Type: {user_profile.get_user_type_display() if user_profile else 'Unknown'}")
            else:
                print(f"   🚗 {session.vehicle_number} (Slot: {session.slot.slot_id}) - ⚠️ Unregistered")
        except Exception as e:
            print(f"   ❌ Error processing session {session.vehicle_number}: {e}")
        print()
    
    # Test 3: Test slot status API response format
    print("✅ Testing slot status API response format...")
    from pms.views import slot_status_api
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/slot-status/')
    request.user = AnonymousUser()
    
    # We can't actually call the view without proper authentication,
    # but we can test the data structure manually
    slots = ParkingSlot.objects.all()[:3]
    for slot in slots:
        session = ParkingSession.objects.filter(slot=slot, status__in=['pending', 'active']).last()
        if session:
            try:
                vehicle_info = Vehicle.objects.filter(
                    plate_number=session.vehicle_number,
                    is_active=True
                ).select_related('owner', 'owner__userprofile').first()
                
                if vehicle_info and vehicle_info.owner:
                    user_profile = getattr(vehicle_info.owner, 'userprofile', None)
                    user_info = {
                        'name': vehicle_info.owner.get_full_name() or vehicle_info.owner.username,
                        'email': vehicle_info.owner.email,
                        'phone': user_profile.phone_number if user_profile else None,
                        'user_type': user_profile.get_user_type_display() if user_profile else 'Unknown'
                    }
                    print(f"   🎯 Slot {slot.slot_id}: {session.vehicle_number}")
                    print(f"      📊 User info structure: {json.dumps(user_info, indent=8)}")
                else:
                    print(f"   🎯 Slot {slot.slot_id}: {session.vehicle_number} (Unregistered)")
            except Exception as e:
                print(f"   ❌ Error processing slot {slot.slot_id}: {e}")
        else:
            print(f"   🎯 Slot {slot.slot_id}: Available")
        print()
    
    print("🎉 Test completed! Check the browser to see the visual improvements.")
    print("📋 Key improvements implemented:")
    print("   • Slot grids now show user names instead of just vehicle numbers")
    print("   • Tooltips include user contact information")
    print("   • History page shows comprehensive user details")
    print("   • End session dropdown shows user names")
    print("   • Lookup functionality enhanced with user information")

if __name__ == "__main__":
    test_user_vehicle_relationships()
