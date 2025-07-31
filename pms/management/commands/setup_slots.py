"""
Django management command to set up parking slots from configuration
Usage: python manage.py setup_slots [options]
"""

from django.core.management.base import BaseCommand, CommandError
from personal.models import ParkingSlot
import yaml
from pathlib import Path

class Command(BaseCommand):
    help = 'Set up parking slots from configuration file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            default='detector_config.yaml',
            help='Path to detector configuration file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing slots before creating new ones'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating slots'
        )

    def handle(self, *args, **options):
        config_file = Path(options['config'])
        
        if not config_file.exists():
            raise CommandError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise CommandError(f"Failed to load configuration: {e}")
        
        if 'parking_slots' not in config:
            raise CommandError("No parking_slots configuration found")
        
        slots_config = config['parking_slots']
        
        if options['dry_run']:
            self.show_dry_run(slots_config)
            return
        
        if options['clear']:
            self.clear_existing_slots()
        
        self.create_slots(slots_config)

    def show_dry_run(self, slots_config):
        """Show what would be created in dry run mode"""
        self.stdout.write(
            self.style.SUCCESS(f'Dry run mode - would create {len(slots_config)} slots:')
        )
        
        zones = {}
        for slot_config in slots_config:
            slot_id = slot_config['id']
            zone = slot_config.get('zone', 'Unknown')
            coords = slot_config['coords']
            priority = slot_config.get('priority', 1)
            
            if zone not in zones:
                zones[zone] = []
            zones[zone].append({
                'id': slot_id,
                'coords': coords,
                'priority': priority
            })
        
        for zone, slots in zones.items():
            self.stdout.write(f"\nZone {zone}:")
            for slot in slots:
                self.stdout.write(
                    f"  - {slot['id']}: {slot['coords']} (priority: {slot['priority']})"
                )

    def clear_existing_slots(self):
        """Clear existing parking slots"""
        count = ParkingSlot.objects.count()
        if count > 0:
            self.stdout.write(
                self.style.WARNING(f'Clearing {count} existing slots...')
            )
            ParkingSlot.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Existing slots cleared')
            )

    def create_slots(self, slots_config):
        """Create parking slots from configuration"""
        created_count = 0
        updated_count = 0
        
        for slot_config in slots_config:
            slot_id = slot_config['id']
            
            # Check if slot already exists
            slot, created = ParkingSlot.objects.get_or_create(
                slot_id=slot_id,
                defaults={
                    'is_occupied': False,
                    'is_reserved': False
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created slot: {slot_id}")
            else:
                updated_count += 1
                self.stdout.write(f"Updated slot: {slot_id}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSlot setup complete: {created_count} created, {updated_count} updated'
            )
        )
        
        # Show summary by zone
        self.show_summary(slots_config)

    def show_summary(self, slots_config):
        """Show summary of created slots"""
        zones = {}
        for slot_config in slots_config:
            zone = slot_config.get('zone', 'Unknown')
            if zone not in zones:
                zones[zone] = 0
            zones[zone] += 1
        
        self.stdout.write("\nSlots by zone:")
        for zone, count in zones.items():
            self.stdout.write(f"  Zone {zone}: {count} slots")
        
        total_slots = ParkingSlot.objects.count()
        available_slots = ParkingSlot.objects.filter(
            is_occupied=False, 
            is_reserved=False
        ).count()
        
        self.stdout.write(f"\nTotal slots in database: {total_slots}")
        self.stdout.write(f"Available slots: {available_slots}")
        self.stdout.write(f"Occupied/Reserved slots: {total_slots - available_slots}")
