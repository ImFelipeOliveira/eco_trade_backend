from django.contrib.auth import authenticate

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from api.models import ComercioProfile, ProdutorProfile, User
from api.serializers import ComercioSerializer, ProdutorSerializer
from rest_framework.authtoken.models import Token


class AuthenticationService:
    def login(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(username=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            if user.role == "merchant":
                user_data = ComercioSerializer(user).data
            else:
                user_data = ProdutorSerializer(user).data

            return {"token": token.key, "user": user_data}

        raise APIException(
            "Email ou password incorretos.", code=status.HTTP_401_UNAUTHORIZED
        )

    @transaction.atomic
    def signup_merchant(self, data):
        if User.objects.filter(email=data.get("email")).exists():
            raise APIException("Email já existe.", code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=data.get("email"),
            email=data.get("email"),
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            role=User.Role.COMERCIO,
        )

        user.set_password(data.get("password"))
        user.save()

        address_data = data.get("address", {})
        location_data = data.get("location", {})

        if not all([address_data, location_data]):
            raise APIException(
                "Dados de endereço e localização são obrigatórios.",
                code=status.HTTP_400_BAD_REQUEST,
            )

        ComercioProfile.objects.create(
            user=user,
            tax_id=data.get("tax_id"),
            legal_name=data.get("legal_name"),
            street=address_data.get("street", ""),
            number=address_data.get("number", ""),
            neighborhood=address_data.get("neighborhood", ""),
            city=address_data.get("city", ""),
            state=address_data.get("state", ""),
            zip_code=address_data.get("zip_code", ""),
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0),
        )

        token = Token.objects.create(user=user)
        return {"token": token.key, "user": ComercioSerializer(user).data}

    @transaction.atomic
    def signup_producer(self, data):
        if User.objects.filter(email=data.get("email")).exists():
            return APIException(
                {"error": "Este email já está em uso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User(
            username=data.get("email"),
            email=data.get("email"),
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            role="producer",
        )
        user.set_password(data.get("password"))
        user.save()

        ProdutorProfile.objects.create(
            user=user,
            cpf=data.get("cpf"),
            collection_capacity_kg=data.get("collection_capacity_kg", 0),
            accepted_waste_types=data.get("accepted_waste_types", []),
        )

        token = Token.objects.create(user=user)
        return {"token": token.key, "user": ProdutorSerializer(user).data}
