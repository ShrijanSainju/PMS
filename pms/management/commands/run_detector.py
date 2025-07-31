"""
Django management command to run the enhanced parking detector
Usage: python manage.py run_detector [options]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

class Command(BaseCommand):
    help = 'Run the enhanced OpenCV parking detector'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            default='detector_config.yaml',
            help='Path to detector configuration file'
        )
        parser.add_argument(
            '--no-video',
            action='store_true',
            help='Run detector without video display (headless mode)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run detector as a background daemon'
        )
        parser.add_argument(
            '--stop',
            action='store_true',
            help='Stop running detector daemon'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Check detector daemon status'
        )

    def handle(self, *args, **options):
        detector_script = Path(__file__).parent.parent.parent.parent / 'opencv_enhanced_detector.py'
        pid_file = Path(settings.BASE_DIR) / 'detector.pid'
        
        if options['stop']:
            self.stop_detector(pid_file)
            return
        
        if options['status']:
            self.check_status(pid_file)
            return
        
        if not detector_script.exists():
            raise CommandError(f"Detector script not found: {detector_script}")
        
        # Prepare command arguments
        cmd = [sys.executable, str(detector_script)]
        
        if options['config']:
            cmd.extend(['--config', options['config']])
        
        if options['no_video']:
            cmd.append('--no-video')
        
        if options['daemon']:
            self.run_daemon(cmd, pid_file)
        else:
            self.run_interactive(cmd)

    def run_interactive(self, cmd):
        """Run detector in interactive mode"""
        self.stdout.write(
            self.style.SUCCESS('Starting parking detector in interactive mode...')
        )
        self.stdout.write(f"Command: {' '.join(cmd)}")
        
        try:
            # Run the detector
            process = subprocess.Popen(cmd)
            process.wait()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nDetector stopped by user')
            )
        except Exception as e:
            raise CommandError(f"Failed to run detector: {e}")

    def run_daemon(self, cmd, pid_file):
        """Run detector as a daemon"""
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Check if process exists
                raise CommandError(f"Detector is already running with PID {pid}")
            except OSError:
                # Process doesn't exist, remove stale PID file
                pid_file.unlink()
        
        self.stdout.write(
            self.style.SUCCESS('Starting parking detector as daemon...')
        )
        
        # Add no-video flag for daemon mode
        if '--no-video' not in cmd:
            cmd.append('--no-video')
        
        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Write PID file
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                self.stdout.write(
                    self.style.SUCCESS(f'Detector started successfully with PID {process.pid}')
                )
                self.stdout.write(f"PID file: {pid_file}")
                self.stdout.write("Use 'python manage.py run_detector --stop' to stop the daemon")
            else:
                pid_file.unlink()
                raise CommandError("Detector failed to start")
                
        except Exception as e:
            if pid_file.exists():
                pid_file.unlink()
            raise CommandError(f"Failed to start detector daemon: {e}")

    def stop_detector(self, pid_file):
        """Stop the detector daemon"""
        if not pid_file.exists():
            self.stdout.write(
                self.style.WARNING('No detector daemon is running')
            )
            return
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to terminate the process gracefully
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit for graceful shutdown
            time.sleep(2)
            
            # Check if it's still running
            try:
                os.kill(pid, 0)
                # Still running, force kill
                self.stdout.write(
                    self.style.WARNING('Detector did not stop gracefully, forcing shutdown...')
                )
                os.kill(pid, signal.SIGKILL)
            except OSError:
                # Process is gone
                pass
            
            # Remove PID file
            pid_file.unlink()
            
            self.stdout.write(
                self.style.SUCCESS(f'Detector daemon stopped (PID {pid})')
            )
            
        except OSError as e:
            if e.errno == 3:  # No such process
                pid_file.unlink()
                self.stdout.write(
                    self.style.WARNING('Detector process was not running, cleaned up PID file')
                )
            else:
                raise CommandError(f"Failed to stop detector: {e}")
        except Exception as e:
            raise CommandError(f"Failed to stop detector: {e}")

    def check_status(self, pid_file):
        """Check detector daemon status"""
        if not pid_file.exists():
            self.stdout.write(
                self.style.WARNING('No detector daemon is running')
            )
            return
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            try:
                os.kill(pid, 0)
                self.stdout.write(
                    self.style.SUCCESS(f'Detector daemon is running with PID {pid}')
                )
                
                # Try to get process info
                try:
                    import psutil
                    process = psutil.Process(pid)
                    self.stdout.write(f"Status: {process.status()}")
                    self.stdout.write(f"CPU: {process.cpu_percent():.1f}%")
                    self.stdout.write(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
                    self.stdout.write(f"Started: {process.create_time()}")
                except ImportError:
                    self.stdout.write("Install psutil for detailed process information")
                except Exception:
                    pass
                    
            except OSError:
                pid_file.unlink()
                self.stdout.write(
                    self.style.ERROR(f'Detector daemon with PID {pid} is not running (cleaned up stale PID file)')
                )
                
        except Exception as e:
            raise CommandError(f"Failed to check detector status: {e}")

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signal"""
        self.stdout.write(
            self.style.WARNING('\nReceived interrupt signal, stopping detector...')
        )
        sys.exit(0)
