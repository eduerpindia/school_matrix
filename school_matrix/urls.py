# school_matrix/urls.py
from django.contrib import admin
# Temporary debug code - remove after fixing
from django.urls import path, include
from django.http import JsonResponse

def debug_urls(request):
    from django.urls import get_resolver
    resolver = get_resolver()
    patterns = []
    for pattern in resolver.url_patterns:
        patterns.append(str(pattern.pattern))
    return JsonResponse({'url_patterns': patterns})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('debug-urls/', debug_urls, name='debug-urls'),  # Remove this after debugging
]
