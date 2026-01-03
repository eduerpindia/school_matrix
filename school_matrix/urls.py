from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


# Temporary debug code
def debug_urls(request):
    from django.urls import get_resolver
    resolver = get_resolver()
    patterns = [str(pattern.pattern) for pattern in resolver.url_patterns]
    return JsonResponse({'url_patterns': patterns})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('debug-urls/', debug_urls, name='debug-urls'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
