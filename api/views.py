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
    SchedulingSerializer
)
# View para listar todos os Comércios
class ComercioListView(generics.ListAPIView):
    # 1. Vai à base de dados buscar apenas os utilizadores com perfil de comércio
    queryset = User.objects.filter(role='merchant')
    # 2. Entrega esses dados ao nosso tradutor de Comércio
    serializer_class = ComercioSerializer

# View para listar todos os Produtores
class ProdutorListView(generics.ListAPIView):
    queryset = User.objects.filter(role='producer')
    serializer_class = ProdutorSerializer

class LoginView(APIView):
    def post(self, request):
        # 1. Pega no email e password que o Flutter enviou
        email = request.data.get('email')
        password = request.data.get('password')

        # 2. Tenta fazer o login no banco de dados
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # 3. Se as credenciais estiverem corretas, cria ou pega o Token dele
            token, created = Token.objects.get_or_create(user=user)
            
            # 4. Descobre se é um Comércio ou Produtor para usar o tradutor certo
            if user.role == 'merchant':
                user_data = ComercioSerializer(user).data
            else:
                user_data = ProdutorSerializer(user).data

            # 5. Devolve o JSON no formato exato que o Flutter espera!
            return Response({
                'token': token.key,
                'user': user_data
            })
        else:
            return Response({"error": "Email ou password incorretos."}, status=status.HTTP_401_UNAUTHORIZED)
        
class ComercioSignUpView(APIView):
    @transaction.atomic # Garante que o User e o Profile são criados juntos ou nenhum é criado
    def post(self, request):
        data = request.data
        
        # 1. Verificar se o email já existe
        if User.objects.filter(email=data.get('email')).exists():
            return Response({"error": "Este email já está em uso."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Criar o Utilizador Base
        user = User(
            username=data.get('email'),
            email=data.get('email'),
            name=data.get('name'),
            phone_number=data.get('phone_number'),
            role='merchant'
        )
        # É OBRIGATÓRIO usar set_password para a password ficar encriptada na base de dados!
        user.set_password(data.get('password'))
        user.save()
        
        # 3. Extrair as "pastas" de endereço e localização do JSON
        address_data = data.get('address', {})
        location_data = data.get('location', {})
        
        # 4. Criar o Perfil de Comércio e ligá-lo ao utilizador
        ComercioProfile.objects.create(
            user=user,
            tax_id=data.get('tax_id'),
            legal_name=data.get('legal_name'),
            street=address_data.get('street', ''),
            number=address_data.get('number', ''),
            neighborhood=address_data.get('neighborhood', ''),
            city=address_data.get('city', ''),
            state=address_data.get('state', ''),
            zip_code=address_data.get('zip_code', ''),
            latitude=location_data.get('latitude', 0.0),
            longitude=location_data.get('longitude', 0.0)
        )
        
        # 5. Gerar o Token e devolver a resposta de sucesso
        token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'user': ComercioSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class ProdutorSignUpView(APIView):
    @transaction.atomic
    def post(self, request):
        data = request.data
        
        if User.objects.filter(email=data.get('email')).exists():
            return Response({"error": "Este email já está em uso."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User(
            username=data.get('email'),
            email=data.get('email'),
            name=data.get('name'),
            phone_number=data.get('phone_number'),
            role='producer'
        )
        user.set_password(data.get('password'))
        user.save()
        
        ProdutorProfile.objects.create(
            user=user,
            cpf=data.get('cpf'),
            collection_capacity_kg=data.get('collection_capacity_kg', 0),
            accepted_waste_types=data.get('accepted_waste_types', [])
        )
        
        token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'user': ProdutorSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
class LoteListCreateView(generics.ListCreateAPIView):
    serializer_class = LoteSerializer
    
    # Exige que o Flutter envie um Token válido para usar esta rota
    permission_classes = [permissions.IsAuthenticated]

    # Função 1: O que fazer quando o Flutter pedir a lista (GET)
    def get_queryset(self):
        # Retorna apenas os lotes que estão "ativos" E cuja data limite é maior ou igual a agora
        return Lote.objects.filter(
            status='active',
            limit_date__gte=timezone.now()
        ).order_by('-created_at') # Mostra os mais recentes primeiro

    # Função 2: O que fazer quando o Flutter enviar um lote novo (POST)
    def perform_create(self, serializer):
        # 1. Trava de segurança: Se não for comércio, é bloqueado na hora!
        if self.request.user.role != 'merchant':
            raise PermissionDenied("Apenas contas de Comércio podem criar lotes de resíduos.")
            
        # 2. Se for comércio, salva normalmente
        serializer.save(comercio=self.request.user)

class AgendarColetaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # Garante que se algo der errado, nada é salvo pela metade
    def post(self, request, lote_id):
        # 1. Trava de segurança: Apenas Produtores podem agendar!
        if request.user.role != 'producer':
            raise PermissionDenied("Apenas contas de Produtor podem agendar coletas.")
        
        # 2. Procura o lote pelo ID que veio na URL
        lote = get_object_or_404(Lote, id=lote_id)

        # 3. Verifica se o lote ainda está disponível
        if lote.status != 'active':
            return Response(
                {"error": "Este lote já foi agendado ou não está mais disponível."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Cria o Agendamento ligando o lote ao produtor atual
        agendamento = Scheduling.objects.create(
            lote=lote,
            produtor=request.user,
            status='pending',
            # O Flutter pode enviar a data proposta no corpo da requisição
            proposed_date=request.data.get('proposed_date') 
        )

        # 5. Muda o status do lote para que ele suma da tela principal
        lote.status = 'scheduled'
        lote.save()

        # 6. Devolve o agendamento montadinho
        return Response(SchedulingSerializer(agendamento).data, status=status.HTTP_201_CREATED)
    
class MeusLotesView(generics.ListAPIView):
    serializer_class = LoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # O Django olha para o Token, descobre quem é o usuário, 
        # e devolve apenas os lotes criados por ele.
        return Lote.objects.filter(comercio=self.request.user).order_by('-created_at')

class MinhasColetasView(generics.ListAPIView):
    serializer_class = SchedulingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Devolve apenas os agendamentos feitos pelo Produtor logado.
        return Scheduling.objects.filter(produtor=self.request.user).order_by('-created_at')
    
class LoteDetailView(generics.RetrieveDestroyAPIView):
    queryset = Lote.objects.all()
    # Coloque o nome exato do Serializer que você usou na LoteListCreateView
    serializer_class = LoteSerializer