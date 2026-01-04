from datetime import date, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import School, SchoolSession


@receiver(post_save, sender=School)
def create_default_session_for_school(sender, instance: School, created, **kwargs):
    if not created:
        return

    today = timezone.now().date()
    start_month = instance.academic_year_start_month or 4

    if today.month >= start_month:
        start_year = today.year
        end_year = today.year + 1
    else:
        start_year = today.year - 1
        end_year = today.year

    start_date = date(start_year, start_month, 1)
    next_start_date = date(start_year + 1, start_month, 1)
    end_date = next_start_date - timedelta(days=1)

    session_name = f"{start_year}-{str(end_year)[-2:]}"

    session, created_session = SchoolSession.objects.get_or_create(
        school=instance,
        name=session_name,
        defaults={
            'start_date': start_date,
            'end_date': end_date,
            'is_current': True,
        }
    )

    if not session.is_current:
        session.is_current = True
        session.save()
