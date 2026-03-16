from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token

from .models import User, ComercioProfile, ProdutorProfile, Lote, Scheduling
from .serializers import (
    ComercioSerializer,
    ProdutorSerializer,
    LoteSerializer,
    SchedulingSerializer,
)

from services.authentication_service import AuthenticationService


class ComercioListView(generics.ListAPIView):
    queryset = User.objects.filter(role="merchant")
    serializer_class = ComercioSerializer


class ProdutorListView(generics.ListAPIView):
    queryset = User.objects.filter(role="producer")
    serializer_class = ProdutorSerializer


class LoginView(APIView):
    def post(self, request):
        data = request.data
        result = AuthenticationService().login(data)
        return Response(result)


class ComercioSignUpView(APIView):
    def post(self, request):
        data = request.data

        result = AuthenticationService().signup_merchant(data)
        return Response(result, status=status.HTTP_201_CREATED)


class ProdutorSignUpView(APIView):
    @transaction.atomic
    def post(self, request):
        data = request.data

        result = AuthenticationService().signup_producer(data)
        return Response(result, status=status.HTTP_201_CREATED)


class LoteListCreateView(generics.ListCreateAPIView):
    serializer_class = LoteSerializer

    # Exige que o Flutter envie um Token válido para usar esta rota
    permission_classes = [permissions.IsAuthenticated]

    # Função 1: O que fazer quando o Flutter pedir a lista (GET)
    def get_queryset(self):
        # Retorna apenas os lotes que estão "ativos" E cuja data limite é maior ou igual a agora
        return Lote.objects.filter(
            status="active", limit_date__gte=timezone.now()
        ).order_by(
            "-created_at"
        )  # Mostra os mais recentes primeiro

    # Função 2: O que fazer quando o Flutter enviar um lote novo (POST)
    def perform_create(self, serializer):
        # 1. Trava de segurança: Se não for comércio, é bloqueado na hora!
        if self.request.user.role != "merchant":
            raise PermissionDenied(
                "Apenas contas de Comércio podem criar lotes de resíduos."
            )

        # 2. Se for comércio, salva normalmente
        serializer.save(comercio=self.request.user)


class AgendarColetaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic  # Garante que se algo der errado, nada é salvo pela metade
    def post(self, request, lote_id):
        # 1. Trava de segurança: Apenas Produtores podem agendar!
        if request.user.role != "producer":
            raise PermissionDenied("Apenas contas de Produtor podem agendar coletas.")

        # 2. Procura o lote pelo ID que veio na URL
        lote = get_object_or_404(Lote, id=lote_id)

        # 3. Verifica se o lote ainda está disponível
        if lote.status != "active":
            return Response(
                {"error": "Este lote já foi agendado ou não está mais disponível."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Cria o Agendamento ligando o lote ao produtor atual
        agendamento = Scheduling.objects.create(
            lote=lote,
            produtor=request.user,
            status="pending",
            # O Flutter pode enviar a data proposta no corpo da requisição
            proposed_date=request.data.get("proposed_date"),
        )

        # 5. Muda o status do lote para que ele suma da tela principal
        lote.status = "scheduled"
        lote.save()

        # 6. Devolve o agendamento montadinho
        return Response(
            SchedulingSerializer(agendamento).data, status=status.HTTP_201_CREATED
        )


class MeusLotesView(generics.ListAPIView):
    serializer_class = LoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # O Django olha para o Token, descobre quem é o usuário,
        # e devolve apenas os lotes criados por ele.
        return Lote.objects.filter(comercio=self.request.user).order_by("-created_at")


class MinhasColetasView(generics.ListAPIView):
    serializer_class = SchedulingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Devolve apenas os agendamentos feitos pelo Produtor logado.
        return Scheduling.objects.filter(produtor=self.request.user).order_by(
            "-created_at"
        )
