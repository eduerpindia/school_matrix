import jwt
from django.conf import settings
from datetime import datetime, timedelta


def create_jwt_token(user, tenant):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'tenant_id': tenant.id,
        'tenant_code': tenant.school_code,  # Store tenant code in JWT
        'exp': datetime.utcnow() + timedelta(days=settings.JWT_EXPIRATION_DAYS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token

def create_refresh_token(user):
    payload = {
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=settings.JWT_EXPIRATION_DAYS * 2),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token

def verify_jwt_token(token):
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.InvalidTokenError:
        return None