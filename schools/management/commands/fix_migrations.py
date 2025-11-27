from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = 'Fix migration issues step by step'

    def handle(self, *args, **options):
        self.stdout.write('Step 1: Creating initial migrations...')
        
        # Create migrations for each app in correct order
        call_command('makemigrations', 'users')
        call_command('makemigrations', 'schools')
        call_command('makemigrations', 'core')
        
        self.stdout.write('Step 2: Applying to public schema...')
        call_command('migrate_schemas', '--shared')
        
        self.stdout.write('Step 3: Creating remaining migrations...')
        call_command('makemigrations')
        
        self.stdout.write('Step 4: Applying all migrations...')
        call_command('migrate_schemas', '--shared')
        
        self.stdout.write(self.style.SUCCESS('✅ Migrations completed successfully!'))