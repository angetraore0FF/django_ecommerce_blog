from rest_framework import serializers
from shop.models import Montre, Accessoire, Marque, CategorieAccessoire
from .models import ProductReview
from django.contrib.auth import get_user_model
from shop.models import CustomUser  # Importez votre modèle CustomUser


User = get_user_model()

class MarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['id', 'nom', 'logo']

class CategorieAccessoireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieAccessoire
        fields = ['id', 'nom', 'slug', 'image']

class MontreSerializer(serializers.ModelSerializer):
    marque = MarqueSerializer()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Montre
        fields = ['id', 'nom', 'marque', 'description', 'prix', 'genre', 
                 'mouvement', 'disponible', 'stock', 'images']

    def get_images(self, obj):
        return [img.image.url for img in obj.images.all()]

class AccessoireSerializer(serializers.ModelSerializer):
    categorie = CategorieAccessoireSerializer()

    class Meta:
        model = Accessoire
        fields = ['id', 'nom', 'categorie', 'marque', 'description', 
                 'prix', 'image', 'en_stock', 'stock']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user','created_at']

    def create(self, validated_data):
        # Ajoute automatiquement l'utilisateur connecté
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'email_verified']
        extra_kwargs = {
            'password': {'write_only': True},
            'email_verified': {'read_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)