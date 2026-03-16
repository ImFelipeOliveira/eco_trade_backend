from django.contrib import admin
from django.urls import path, include

# 1. Importe estas duas bibliotecas mágicas
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), # As nossas rotas!
]

# 2. Adicione esta linha no final para o Django servir as imagens!
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)