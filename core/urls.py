from django.contrib import admin
from django.urls import path, include # Adicionámos o 'include' aqui!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Dizemos ao Django: "Tudo o que começar por 'api/', procura no ficheiro api.urls"
    path('api/', include('api.urls')),
]