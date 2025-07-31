# Generated manually to update existing admin users to manager

from django.db import migrations


def update_admin_to_manager(apps, schema_editor):
    """Update all existing 'admin' user types to 'manager'"""
    UserProfile = apps.get_model('pms', 'UserProfile')
    
    # Update all admin users to manager
    admin_profiles = UserProfile.objects.filter(user_type='admin')
    updated_count = admin_profiles.update(user_type='manager')
    
    if updated_count > 0:
        print(f"Updated {updated_count} admin users to manager users.")
    else:
        print("No admin users found to update.")


def reverse_manager_to_admin(apps, schema_editor):
    """Reverse operation: update manager users back to admin (if needed)"""
    UserProfile = apps.get_model('pms', 'UserProfile')
    
    # This is a reverse operation - we'll update all managers back to admin
    # Note: This might not be perfect since we don't know which managers were originally admins
    manager_profiles = UserProfile.objects.filter(user_type='manager')
    updated_count = manager_profiles.update(user_type='admin')
    
    if updated_count > 0:
        print(f"Reversed {updated_count} manager users back to admin users.")
    else:
        print("No manager users found to reverse.")


class Migration(migrations.Migration):

    dependencies = [
        ('pms', '0015_rename_admin_to_manager'),
    ]

    operations = [
        migrations.RunPython(
            update_admin_to_manager,
            reverse_manager_to_admin,
        ),
    ]
