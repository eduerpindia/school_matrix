 # core/custom_permission.py

from rest_framework.permissions import BasePermission
from .permission_utils import has_module

class BaseModulePermission(BasePermission):
    module_required_name = None
    message = 'Module access denied'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            self.message = 'Authentication required'
            return False

        module_name = self.module_required_name or getattr(view, 'module_required', None)
        if not module_name:
            self.message = 'Configuration error: module name not provided'
            return False

        allowed = has_module(user, module_name)
        if not allowed:
            self.message = f'Module access denied: {module_name}'
        return allowed

class StudentsModulePermission(BaseModulePermission):
    module_required_name = 'students'

class TeachersModulePermission(BaseModulePermission):
    module_required_name = 'teachers'

class AttendanceModulePermission(BaseModulePermission):
    module_required_name = 'attendance'

class FeesModulePermission(BaseModulePermission):
    module_required_name = 'fees'

class ClassesModulePermission(BaseModulePermission):
    module_required_name = 'classes'

class ExaminationsModulePermission(BaseModulePermission):
    module_required_name = 'examinations'

class LibraryModulePermission(BaseModulePermission):
    module_required_name = 'library'