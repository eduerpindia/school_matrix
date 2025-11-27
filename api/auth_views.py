from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import connection
from django.contrib.auth import authenticate
from core.permission_utils import effective_module_permissions
from core.models import Module
from api.jwt_utils import create_jwt_token, create_refresh_token
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]  # ✅ Allow anyone to access login
    authentication_classes = []      # ✅ Disable all authentication for login

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        logger.info(f"🔍 Login attempt for email: {email}")
        logger.info(f"🔍 Request tenant: {getattr(request, 'tenant', 'None')}")
        logger.info(f"🔍 Connection schema: {getattr(connection, 'schema_name', 'unknown')}")

        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Debug: Check current schema and available users
            current_schema = getattr(connection, 'schema_name', 'unknown')
            user_count = User.objects.count()
            available_emails = list(User.objects.values_list('email', flat=True)[:5])  # First 5 only
            
            logger.info(f"🔍 Schema: {current_schema}, User count: {user_count}")
            logger.info(f"🔍 Available emails: {available_emails}")

            # Use Django's authenticate function
            user = authenticate(request=request, username=email, password=password)
            
            if user is not None:
                logger.info(f"✅ Authentication successful for user: {user.email}")
                
                # Create JWT tokens
                access_token = create_jwt_token(user, request.tenant)
                refresh_token = create_refresh_token(user)

                # Get module permissions
                mods = sorted(list(effective_module_permissions(user)))
                
                # Build module access map
                modules = Module.objects.filter(name__in=mods, is_active=True)
                modules_access_map = {
                    m.name: {
                        'display_name': m.display_name,
                        'icon': m.icon,
                        'can_view': True,
                        'can_add': True,
                        'can_edit': True,
                        'can_delete': True,
                        'can_import': True,
                        'can_export': True,
                    } for m in modules
                }

                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'tokens': {
                        'access': access_token,
                        'refresh': refresh_token
                    },
                    'user': {
                        'id': user.id,
                        'name': user.get_full_name(),
                        'email': user.email,
                        'user_type': user.user_type
                    },
                    'tenant': {
                        'id': request.tenant.id,
                        'name': request.tenant.name,
                        'schema': request.tenant.schema_name
                    },
                    'modules': mods,
                    'modules_access_map': modules_access_map,
                    'debug': {
                        'schema': current_schema,
                        'user_count': user_count
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"❌ Authentication failed for email: {email}")
                return Response({
                    'success': False,
                    'error': 'Invalid email or password',
                    'debug': {
                        'available_users': available_emails,
                        'schema': current_schema,
                        'tenant': request.tenant.school_code if hasattr(request, 'tenant') else 'none'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Authentication error',
                'debug_info': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from api.jwt_utils import verify_jwt_token
            payload = verify_jwt_token(refresh_token)
            
            if not payload or payload.get('type') != 'refresh':
                return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
                
            user = User.objects.get(id=payload['user_id'])
            
            # Create new access token
            access_token = create_jwt_token(user, request.tenant)
            
            return Response({
                'access_token': access_token
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]  # Allow logout without authentication
    
    def post(self, request):
        # With JWT, logout is client-side (token deletion)
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)