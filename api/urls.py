from django.urls import path
from .views import (
    ComercioListView, 
    ProdutorListView, 
    LoginView, 
    ComercioSignUpView, 
    ProdutorSignUpView,
    LoteListCreateView,
    AgendarColetaView,
    MeusLotesView,
    MinhasColetasView
)

urlpatterns = [
    # Rotas de Autenticação
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/register/comercio/', ComercioSignUpView.as_view(), name='api-register-comercio'),
    path('auth/register/produtor/', ProdutorSignUpView.as_view(), name='api-register-produtor'),
    
    # Rotas de Listagem
    path('comercios/', ComercioListView.as_view(), name='lista-comercios'),
    path('produtores/', ProdutorListView.as_view(), name='lista-produtores'),

    # Rotas de Lotes
    path('lotes/', LoteListCreateView.as_view(), name='lista-cria-lotes'),

    # Rotas de Lotes e Agendamentos
    path('lotes/', LoteListCreateView.as_view(), name='lista-cria-lotes'),
    path('lotes/<int:lote_id>/agendar/', AgendarColetaView.as_view(), name='agendar-coleta'),

    # Rotas de Lotes e Agendamentos
    path('lotes/', LoteListCreateView.as_view(), name='lista-cria-lotes'),
    path('lotes/<int:lote_id>/agendar/', AgendarColetaView.as_view(), name='agendar-coleta'),
    
    # Rotas de Histórico
    path('meus-lotes/', MeusLotesView.as_view(), name='meus-lotes'),
    path('minhas-coletas/', MinhasColetasView.as_view(), name='minhas-coletas'),
]