from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from shop.models import CustomUser, Montre, Accessoire
from .models import ProductReview
from .serializers import (
    MontreSerializer,
    AccessoireSerializer,
    ProductReviewSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from api import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter


class ProductViewSet(viewsets.ViewSet):
    """Vue combinée pour les montres et accessoires"""
    
    def list(self, request):
        montres = Montre.objects.filter(disponible=True)
        accessoires = Accessoire.objects.filter(en_stock=True)
        
        context = {'request': request}
        data = {
            'montres': MontreSerializer(montres, many=True, context=context).data,
            'accessoires': AccessoireSerializer(accessoires, many=True, context=context).data
        }
        return Response(data)

class MontreViewSet(viewsets.ModelViewSet):
    queryset = Montre.objects.filter(disponible=True)
    serializer_class = MontreSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['marque', 'genre', 'mouvement']

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        montre = self.get_object()
        similar = Montre.objects.filter(
            Q(marque=montre.marque) | Q(genre=montre.genre),
            disponible=True
        ).exclude(id=montre.id)[:4]
        serializer = self.get_serializer(similar, many=True)
        return Response(serializer.data)

class AccessoireViewSet(viewsets.ModelViewSet):
    queryset = Accessoire.objects.filter(en_stock=True)
    serializer_class = AccessoireSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categorie', 'marque']

@extend_schema(
    description="Liste et création d'avis produits",
    parameters=[
        OpenApiParameter(name='product_id', description="Filtrer par produit", required=False, type=int),
    ],
    responses={
        200: ProductReviewSerializer(many=True),
        201: ProductReviewSerializer,
    }
)

class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductReview.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def perform_create(self, serializer):
    if not isinstance(self.request.user, CustomUser):
        raise serializers.ValidationError("Vous devez être connecté avec un compte valide")
    serializer.save(user=self.request.user)



