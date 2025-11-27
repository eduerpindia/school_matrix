from core.models import Module, Permission, UserRole, UserPermission

def effective_module_permissions(user):
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
    return module_name in effective_module_permissions(user)