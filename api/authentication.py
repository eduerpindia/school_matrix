import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework import exceptions
from schools.models import School
from django.db import connection

User = get_user_model()

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
            
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Set tenant from JWT
            tenant_code = payload.get('tenant_code')
            if tenant_code:
                school = School.objects.get(school_code=tenant_code, is_active=True)
                connection.set_tenant(school)
                request.tenant = school
            
            user = User.objects.get(id=payload['user_id'])
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        except School.DoesNotExist:
            raise exceptions.AuthenticationFailed('Tenant not found')