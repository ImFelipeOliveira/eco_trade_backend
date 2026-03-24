from django.contrib import admin
from django.urls import path, include

# 1. Importe estas duas bibliotecas mágicas
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), # As nossas rotas!
]

from django.views.static import serve
from django.urls import re_path

# Serve media files in production/dev
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

handler404 = 'core.views.error_404_handler'
handler500 = 'core.views.error_500_handler'
handler400 = 'core.views.error_400_handler'
handler403 = 'core.views.error_403_handler'