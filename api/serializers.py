from rest_framework import serializers
from .models import User, Lote, Scheduling

# Tradutor para o perfil de Comércio
class ComercioSerializer(serializers.ModelSerializer):
    # A nossa API vai chamar 'uid' ao 'id' do Django para agradar ao Flutter
    uid = serializers.IntegerField(source='id', read_only=True)
    
    # Vamos buscar os dados que estão guardados na tabela secundária do perfil
    tax_id = serializers.CharField(source='comercio_profile.tax_id')
    legal_name = serializers.CharField(source='comercio_profile.legal_name')
    
    # Campos customizados para criar os dicionários (objetos) aninhados
    address = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Esta lista define as chaves exatas que vão ser enviadas para o telemóvel
        fields = ['uid', 'email', 'name', 'phone_number', 'tax_id', 'legal_name', 'address', 'location']

    # Constrói o bloco "address" com a mesma estrutura do Address.fromJson no Dart
    def get_address(self, obj):
        profile = obj.comercio_profile
        return {
            'street': profile.street,
            'number': profile.number,
            'neighborhood': profile.neighborhood,
            'city': profile.city,
            'state': profile.state,
            'zip_code': profile.zip_code,
        }

    # Constrói o bloco "location" com a mesma estrutura do Localizacao.fromJson no Dart
    def get_location(self, obj):
        profile = obj.comercio_profile
        return {
            'latitude': profile.latitude,
            'longitude': profile.longitude,
        }

# Tradutor para o perfil de Produtor
class ProdutorSerializer(serializers.ModelSerializer):
    uid = serializers.IntegerField(source='id', read_only=True)
    cpf = serializers.CharField(source='produtor_profile.cpf')
    collection_capacity_kg = serializers.IntegerField(source='produtor_profile.collection_capacity_kg')
    accepted_waste_types = serializers.ListField(source='produtor_profile.accepted_waste_types')

    class Meta:
        model = User
        fields = ['uid', 'email', 'name', 'phone_number', 'cpf', 'collection_capacity_kg', 'accepted_waste_types']

# Tradutor para os Lotes
class LoteSerializer(serializers.ModelSerializer):
    # O segredo aqui: vamos "embutir" o tradutor do comércio dentro do lote!
    # Assim, quando o Flutter pedir um lote, ele já recebe todos os dados de quem o criou.
    comercio = ComercioSerializer(read_only=True)
    
    # Formatando as datas para o padrão internacional (ISO 8601) que o Dart ama ler
    limit_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id', 'comercio', 'description', 'image_url', 'weight', 
            'limit_date', 'latitude', 'longitude', 'status', 'created_at'
        ]


# Tradutor para os Agendamentos
class SchedulingSerializer(serializers.ModelSerializer):
    # Embutindo os dados do lote e do produtor que vai coletar
    lote = LoteSerializer(read_only=True)
    produtor = ProdutorSerializer(read_only=True)
    
    proposed_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", required=False)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Scheduling
        fields = ['id', 'lote', 'produtor', 'status', 'proposed_date', 'created_at']