#!/usr/bin/env python
"""
Script to create sample parking slots for testing the PMS system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from pms.models import ParkingSlot

def create_sample_slots():
    """Create sample parking slots for testing"""
    
    # Clear existing slots
    ParkingSlot.objects.all().delete()
    print("Cleared existing parking slots")
    
    # Create slots for different zones
    zones = ['A', 'B', 'C', 'P']  # A, B, C for manual assignment, P for video detection
    
    slots_created = 0
    
    for zone in zones:
        for i in range(1, 11):  # 10 slots per zone
            slot_id = f"{zone}{i:02d}"  # A01, A02, ..., B01, B02, etc.
            
            slot = ParkingSlot.objects.create(
                slot_id=slot_id,
                is_occupied=False,
                is_reserved=False
            )
            slots_created += 1
            print(f"Created slot: {slot_id}")
    
    print(f"\nSuccessfully created {slots_created} parking slots")
    print(f"Total slots in database: {ParkingSlot.objects.count()}")
    
    # Show breakdown by zone
    for zone in zones:
        count = ParkingSlot.objects.filter(slot_id__startswith=zone).count()
        print(f"Zone {zone}: {count} slots")

if __name__ == "__main__":
    create_sample_slots()
