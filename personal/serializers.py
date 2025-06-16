# serializers.py
from rest_framework import serializers
from .models import ParkingSlot

class ParkingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSlot
        fields = ['id', 'slot_id', 'is_occupied', 'timestamp']
