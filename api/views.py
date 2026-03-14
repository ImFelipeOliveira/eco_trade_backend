from rest_framework import generics
from .models import User
from .serializers import ComercioSerializer, ProdutorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.db import transaction
from .models import ComercioProfile, ProdutorProfile

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