from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

# 1. Modelo Base de Usuário (Serve tanto para Comércio quanto para Produtor)
class User(AbstractUser):
    class Role(models.TextChoices):
        COMERCIO = 'merchant', 'Comércio'
        PRODUTOR = 'producer', 'Produtor'

    # Campos compartilhados da sua classe AppUser do Dart
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255) # Nome Fantasia ou Nome do Produtor
    phone_number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=Role.choices)

    # Dizemos ao Django para usar o email no login em vez do 'username' padrão
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name', 'role']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


# 2. Perfil Específico do Comércio
class ComercioProfile(models.Model):
    # O OneToOneField garante que cada Usuário tenha apenas um Perfil de Comércio
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='comercio_profile')
    
    tax_id = models.CharField(max_length=18, unique=True) # CNPJ
    legal_name = models.CharField(max_length=255) # Razão Social
    
    # Endereço (Sua classe Address do Dart)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    neighborhood = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=20)
    
    # Localização (Sua classe Localizacao do Dart)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"Perfil Comércio: {self.user.name}"


# 3. Perfil Específico do Produtor
class ProdutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='produtor_profile')
    
    cpf = models.CharField(max_length=14, unique=True)
    collection_capacity_kg = models.IntegerField()
    
    # Como estamos usando o PostgreSQL, podemos usar o ArrayField incrível dele
    # para guardar a lista de strings (accepted_waste_types) nativamente!
    accepted_waste_types = ArrayField(
        models.CharField(max_length=50), 
        blank=True, 
        default=list
    )

    def __str__(self):
        return f"Perfil Produtor: {self.user.name}"
    
# ... (mantenha os modelos User, ComercioProfile e ProdutorProfile lá em cima)

class Lote(models.Model):
    # O Comércio dono do lote
    comercio = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meus_lotes')
    
    # Detalhes do resíduo
    description = models.CharField(max_length=255, default="Lote de Resíduos")
    image_url = models.ImageField(upload_to='residuos/', blank=True, null=True)    
    weight = models.FloatField()
    limit_date = models.DateTimeField()
    
    # Localização exata de onde o lote está
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Status (active, scheduled, completed)
    status = models.CharField(max_length=20, default='active')
    
    # Lista de produtores que clicaram em "Tenho Interesse"
    interested_producers = models.ManyToManyField(User, related_name='interested_lotes', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lote {self.id} - {self.comercio.name} ({self.weight}kg)"


class Scheduling(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        CONFIRMED = 'confirmed', 'Confirmado'
        COMPLETED = 'completed', 'Finalizado'

    # Liga o agendamento a um lote e a um produtor
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='schedulings')
    produtor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meus_agendamentos')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Quando a coleta foi proposta/agendada
    proposed_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agendamento {self.id} - Lote {self.lote.id} ({self.get_status_display()})"