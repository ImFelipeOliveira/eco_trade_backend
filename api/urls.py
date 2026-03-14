from django.urls import path
from .views import (
    ComercioListView, 
    ProdutorListView, 
    LoginView, 
    ComercioSignUpView, 
    ProdutorSignUpView  
)

urlpatterns = [
    # Rotas de Autenticação
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/register/comercio/', ComercioSignUpView.as_view(), name='api-register-comercio'),
    path('auth/register/produtor/', ProdutorSignUpView.as_view(), name='api-register-produtor'),
    
    # Rotas de Listagem
    path('comercios/', ComercioListView.as_view(), name='lista-comercios'),
    path('produtores/', ProdutorListView.as_view(), name='lista-produtores'),
]