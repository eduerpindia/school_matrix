# api/middleware.py
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from schools.models import School
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class TenantHeaderMiddleware(MiddlewareMixin):
    def process_request(self, request):
        print(f"🔄 Processing request: {request.path}")
        
        # Skip for admin endpoints और static files
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/debug-urls/')):
            return None
        
        # Get tenant code from header
        tenant_code = request.headers.get('Tenant-Name') or request.headers.get('X-Tenant-Code')
        print(f"----------tenant_code: {tenant_code}")
        
        # Check if tenant header is missing
        if not tenant_code:
            return JsonResponse({
                'success': False,
                'error': 'Tenant header required',
                'message': 'Tenant-Name header is required for all API requests'
            }, status=400)
        
        try:
            # Find school by code
            school = School.objects.get(school_code=tenant_code, is_active=True)
            
            # ✅ CRITICAL FIX: Properly set tenant using django_tenants
            connection.set_tenant(school)
            
            # Store tenant info in request
            request.tenant = school
            
            print(f"✅ Tenant set: {tenant_code} -> schema: {connection.schema_name}")
            logger.info(f"Tenant set from header: {tenant_code}")
            
        except School.DoesNotExist:
            print(f"❌ School not found: {tenant_code}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid tenant',
                'message': f'School with code {tenant_code} not found'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Error setting tenant: {str(e)}")
            logger.error(f"Error setting tenant from header: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Tenant setup failed',
                'message': 'Failed to set tenant schema'
            }, status=500)
        
        return None

    def process_response(self, request, response):
        # Clean response processing
        try:
            if hasattr(request, 'tenant'):
                print("✅ Request completed for tenant")
        except Exception as e:
            logger.error(f"Error in response processing: {str(e)}")
        return response
