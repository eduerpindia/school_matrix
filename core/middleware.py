# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .models import AcademicYear

class AcademicYearMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Add current academic year to request
        request.current_academic_year = AcademicYear.get_current_academic_year()
    
# # settings.py
# MIDDLEWARE = [
#     # ... other middleware ...
#     'core.middleware.AcademicYearMiddleware',
# ]