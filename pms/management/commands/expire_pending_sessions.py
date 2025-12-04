from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from pms.models import ParkingSession


class Command(BaseCommand):
    help = 'Expire pending parking sessions that have been waiting for more than 30 minutes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout in minutes for pending sessions (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually expiring',
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Find pending sessions older than cutoff time
        expired_sessions = ParkingSession.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        ).select_related('slot')
        
        count = expired_sessions.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No pending sessions to expire.'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would expire {count} session(s):'))
            for session in expired_sessions:
                age_minutes = (timezone.now() - session.created_at).total_seconds() / 60
                self.stdout.write(
                    f'  - {session.session_id}: {session.vehicle_number} in {session.slot.slot_id} '
                    f'(pending for {age_minutes:.1f} minutes)'
                )
        else:
            self.stdout.write(f'Expiring {count} pending session(s)...')
            
            expired_count = 0
            for session in expired_sessions:
                age_minutes = (timezone.now() - session.created_at).total_seconds() / 60
                
                # Change session status to cancelled
                session.status = 'cancelled'
                session.end_time = timezone.now()
                session.save()
                
                # Free up the slot
                session.slot.is_reserved = False
                session.slot.save()
                
                expired_count += 1
                self.stdout.write(
                    f'  ✓ Expired {session.session_id}: {session.vehicle_number} in {session.slot.slot_id} '
                    f'(was pending for {age_minutes:.1f} minutes)'
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {expired_count} session(s) and freed their slots.')
            )
