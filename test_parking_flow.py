#!/usr/bin/env python3
"""
Test script to verify simplified parking flow: Vacant → Reserved → Occupied
"""

import os
import sys
import django
import requests
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from pms.models import ParkingSlot, ParkingSession
from django.utils import timezone

def test_simplified_parking_flow():
    """Test the simplified three-state parking flow"""
    print("=== Testing Simplified Parking Flow ===")
    
    # Test 1: Slot starts as vacant (green)
    print("\n1. Initial state - Slot A1 is vacant (green)...")
    slot = ParkingSlot.objects.get_or_create(slot_id='A1')[0]
    slot.is_occupied = False
    slot.is_reserved = False
    slot.save()
    
    print(f"   ✓ Slot {slot.slot_id}: Vacant (Green)")
    
    # Test 2: Staff assigns vehicle to slot (reserved - yellow)
    print("\n2. Staff assigns vehicle ABC123 to slot A1...")
    session = ParkingSession.objects.create(
        vehicle_number='ABC123',
        slot=slot,
        status='pending'
    )
    slot.is_reserved = True
    slot.save()
    
    print(f"   ✓ Slot {slot.slot_id}: Reserved (Yellow)")
    print(f"   ✓ Session status: {session.status}")
    
    # Test 3: Vehicle arrives and parks (occupied - red)
    print("\n3. Vehicle arrives and parks in slot A1...")
    
    # Call the simplified update_slot API
    api_url = 'http://127.0.0.1:8000/api/update-slot/'
    data = {
        'slot_id': 'A1',
        'is_occupied': True
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=5)
        if response.status_code == 200:
            print("   ✓ API call successful")
            result = response.json()
            print(f"   ✓ Message: {result.get('message', 'No message')}")
        else:
            print(f"   ✗ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ API call error: {e}")
    
    # Check final state
    slot.refresh_from_db()
    session.refresh_from_db()
    
    print(f"\n4. Final state:")
    print(f"   Slot {slot.slot_id}:")
    print(f"     - is_occupied: {slot.is_occupied}")
    print(f"     - is_reserved: {slot.is_reserved}")
    print(f"   Session:")
    print(f"     - status: {session.status}")
    print(f"     - start_time: {session.start_time}")
    
    if slot.is_occupied and not slot.is_reserved and session.status == 'active':
        print("\n   ✓ SUCCESS: Simplified flow completed correctly!")
        print("   ✓ Vacant → Reserved → Occupied transition successful")
        print("   ✓ Session activated with start time")
    else:
        print("\n   ✗ FAILURE: Flow did not complete correctly")
        print("   ✗ Expected: occupied=True, reserved=False, session=active")

def test_three_state_system():
    """Test the three-state system"""
    print("\n=== Testing Three-State System ===")
    
    # Test different slot states
    test_cases = [
        ('A2', False, False, "Vacant (Green)"),
        ('A3', False, True, "Reserved (Yellow)"),
        ('A4', True, False, "Occupied (Red)"),
    ]
    
    for slot_id, is_occupied, is_reserved, expected in test_cases:
        slot = ParkingSlot.objects.get_or_create(slot_id=slot_id)[0]
        slot.is_occupied = is_occupied
        slot.is_reserved = is_reserved
        slot.save()
        
        print(f"   {slot_id}: {expected}")

def test_session_decoupling():
    """Test that session ending is decoupled from slot vacancy"""
    print("\n=== Testing Session Decoupling ===")
    
    # Create a slot with active session
    slot = ParkingSlot.objects.get_or_create(slot_id='B1')[0]
    slot.is_occupied = True
    slot.is_reserved = False
    slot.save()
    
    session = ParkingSession.objects.create(
        vehicle_number='XYZ789',
        slot=slot,
        status='active',
        start_time=timezone.now()
    )
    
    print(f"   ✓ Slot B1: Occupied with active session")
    print(f"   ✓ Session: {session.vehicle_number} - {session.status}")
    
    # Simulate vehicle leaving (slot becomes vacant but session remains active)
    print("\n   Simulating vehicle leaving (slot becomes vacant)...")
    
    api_url = 'http://127.0.0.1:8000/api/update-slot/'
    data = {
        'slot_id': 'B1',
        'is_occupied': False
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=5)
        if response.status_code == 200:
            slot.refresh_from_db()
            session.refresh_from_db()
            
            print(f"   ✓ Slot B1: {'Vacant' if not slot.is_occupied else 'Occupied'}")
            print(f"   ✓ Session: {session.status} (should still be active)")
            
            if not slot.is_occupied and session.status == 'active':
                print("   ✓ SUCCESS: Session remains active when slot becomes vacant")
            else:
                print("   ✗ FAILURE: Session should remain active")
        else:
            print(f"   ✗ API call failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ API call error: {e}")

if __name__ == '__main__':
    print("Parking Management System - Simplified Flow Test")
    print("=" * 60)
    
    test_three_state_system()
    test_simplified_parking_flow()
    test_session_decoupling()
    
    print("\n" + "=" * 60)
    print("Test completed!") 