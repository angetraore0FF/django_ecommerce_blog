from django.urls import path, include
from rest_framework import routers
from knox import views as knox_views
from .api import UserAPI, LoginAPI
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    MontreViewSet,
    AccessoireViewSet,
    ProductReviewViewSet
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView



router = DefaultRouter()
router.register(r'montres', MontreViewSet)
router.register(r'accessoires', AccessoireViewSet)
router.register(r'reviews', ProductReviewViewSet, basename='productreview')

urlpatterns = [
    path('products/', ProductViewSet.as_view({'get': 'list'}), name='products-list'),
    path('', include(router.urls)),
    path('auth/user/', UserAPI.as_view()),
    path('login/', LoginAPI.as_view()),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('register/', UserAPI.as_view(), name='register'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),  # UI Swagger
]