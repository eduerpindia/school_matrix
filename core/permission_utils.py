# core/permission_utils.py

from core.models import Module, Permission, UserRole, UserPermission
from django.contrib.auth import get_user_model

User = get_user_model()


def effective_module_permissions(user):
    """
    Get all effective module permissions for a user
    Returns set of module names
    """
    if getattr(user, 'user_type', '') == 'school_admin':
        return set(Module.objects.filter(is_active=True).values_list('name', flat=True))

    role_codes = set(
        Permission.objects.filter(
            role__in=UserRole.objects.filter(user=user, is_active=True).values('role_id')
        ).values_list('codename', flat=True)
    )

    if 'ALL_MODULES' in role_codes:
        return set(Module.objects.filter(is_active=True).values_list('name', flat=True))

    eff = {c for c in role_codes if c != 'ALL_MODULES'}

    for up in UserPermission.objects.filter(user=user):
        code = up.permission.codename
        if code == 'ALL_MODULES':
            if up.granted:
                return set(Module.objects.filter(is_active=True).values_list('name', flat=True))
            else:
                eff.clear()
                continue
        if up.granted:
            eff.add(code)
        else:
            eff.discard(code)

    active = set(Module.objects.filter(is_active=True).values_list('name', flat=True))
    return eff.intersection(active)


def has_module(user, module_name):
    """
    Check if user has access to specific module
    """
    return module_name in effective_module_permissions(user)


# ========== NEW HELPER FUNCTIONS ==========

def assign_modules_to_user(user, module_names):
    """
    Assign multiple modules to a user via UserPermission
    
    Args:
        user: User instance
        module_names: List of module names ['students', 'teachers', 'attendance']
    
    Returns:
        dict: {
            'success': int,
            'failed': list,
            'errors': dict
        }
    """
    if not isinstance(module_names, list):
        module_names = [module_names]
    
    success_count = 0
    failed = []
    errors = {}
    
    for module_name in module_names:
        try:
            # Get or create Permission with module codename
            permission, created = Permission.objects.get_or_create(
                codename=module_name,
                defaults={'name': f'Can access {module_name} module'}
            )
            
            # Create or update UserPermission
            user_permission, created = UserPermission.objects.update_or_create(
                user=user,
                permission=permission,
                defaults={'granted': True}
            )
            
            success_count += 1
            
        except Exception as e:
            failed.append(module_name)
            errors[module_name] = str(e)
    
    return {
        'success': success_count,
        'failed': failed,
        'errors': errors
    }


def remove_modules_from_user(user, module_names):
    """
    Remove module access from user
    
    Args:
        user: User instance
        module_names: List of module names to remove
    
    Returns:
        int: Number of modules removed
    """
    if not isinstance(module_names, list):
        module_names = [module_names]
    
    # Set granted=False for these modules
    updated_count = UserPermission.objects.filter(
        user=user,
        permission__codename__in=module_names
    ).update(granted=False)
    
    return updated_count


def assign_role_to_user(user, role_name):
    """
    Assign a role to user
    
    Args:
        user: User instance
        role_name: Role name string (e.g., 'teacher', 'student', 'admin')
    
    Returns:
        tuple: (UserRole instance or None, error message or None)
    """
    from core.models import Role
    
    try:
        role = Role.objects.get(name=role_name, is_active=True)
        
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={'is_active': True}
        )
        
        # Ensure is_active=True
        if not created and not user_role.is_active:
            user_role.is_active = True
            user_role.save()
        
        return user_role, None
        
    except Role.DoesNotExist:
        return None, f"Role '{role_name}' does not exist"
    
    except Exception as e:
        return None, str(e)


def remove_role_from_user(user, role_name):
    """
    Remove role from user (set is_active=False)
    
    Args:
        user: User instance
        role_name: Role name string
    
    Returns:
        bool: True if removed successfully
    """
    from core.models import Role
    
    try:
        role = Role.objects.get(name=role_name)
        
        updated = UserRole.objects.filter(
            user=user,
            role=role
        ).update(is_active=False)
        
        return updated > 0
        
    except Role.DoesNotExist:
        return False


def get_user_modules(user):
    """
    Get list of module names user can access
    
    Args:
        user: User instance
    
    Returns:
        list: List of module names
    """
    return list(effective_module_permissions(user))


def get_user_roles(user):
    """
    Get all active roles assigned to user
    
    Args:
        user: User instance
    
    Returns:
        QuerySet: Role objects
    """
    from core.models import Role
    
    if not user or not user.is_authenticated:
        return Role.objects.none()
    
    return Role.objects.filter(
        id__in=UserRole.objects.filter(
            user=user,
            is_active=True
        ).values_list('role_id', flat=True)
    )


def bulk_assign_modules_to_role(role, module_names):
    """
    Bulk assign modules to a role
    
    Args:
        role: Role instance
        module_names: List of module names
    
    Returns:
        dict: Result summary
    """
    results = {
        'success': [],
        'failed': [],
        'errors': {}
    }
    
    for module_name in module_names:
        try:
            # Get or create Permission
            permission, created = Permission.objects.get_or_create(
                codename=module_name,
                defaults={'name': f'Can access {module_name} module'}
            )
            
            # Add to role
            role.permissions.add(permission)
            results['success'].append(module_name)
            
        except Exception as e:
            results['failed'].append(module_name)
            results['errors'][module_name] = str(e)
    
    return results


def create_default_teacher_permissions():
    """
    Create default teacher role with standard permissions
    Useful for initial setup
    
    Returns:
        Role: Teacher role instance
    """
    from core.models import Role
    
    # Get or create teacher role
    teacher_role, created = Role.objects.get_or_create(
        name='teacher',
        defaults={
            'description': 'Default teacher role with limited access',
            'is_active': True
        }
    )
    
    # Assign default modules for teachers
    default_modules = ['students', 'attendance', 'classes']
    
    for module_name in default_modules:
        permission, _ = Permission.objects.get_or_create(
            codename=module_name,
            defaults={'name': f'Can access {module_name} module'}
        )
        teacher_role.permissions.add(permission)
    
    return teacher_role


def sync_user_type_with_role(user):
    """
    Automatically assign role based on user_type
    
    Args:
        user: User instance
    
    Returns:
        UserRole or None
    """
    role_mapping = {
        'teacher': 'teacher',
        'student': 'student',
        'parent': 'parent',
        'school_admin': 'admin',
        'principal': 'principal'
    }
    
    user_type = getattr(user, 'user_type', None)
    role_name = role_mapping.get(user_type)
    
    if role_name:
        user_role, error = assign_role_to_user(user, role_name)
        return user_role
    
    return None
