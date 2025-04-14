from django.urls import path
from django.conf import settings  # Ajoutez cette ligne
from django.conf.urls.static import static  # Ajoutez cette ligne
from . import views
from django.contrib.auth import views as auth_views  # Cette ligne est cruciale
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('inscription/', views.register, name='inscription'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

   path('montres/', views.montres, name='montres'),
   path('montres/<int:montre_id>/', views.detail_montre, name='detail_montre'),

    path('panier/', views.voir_panier, name='voir_panier'),
    path('panier/ajouter/<int:montre_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/retirer/<int:item_id>/', views.retirer_du_panier, name='retirer_du_panier'),
    path('panier/modifier/<int:item_id>/', views.modifier_quantite, name='modifier_quantite'),

    path('checkout/', login_required(views.checkout), name='checkout'),
    path('checkout/confirmation/<int:commande_id>/', views.confirmation_commande, name='confirmation_commande'),

    path('appliquer-code-promo/', views.appliquer_code_promo, name='appliquer_code_promo'),
    path('supprimer-code-promo/', views.supprimer_code_promo, name='supprimer_code_promo'),

    path('contact/', views.contact, name='contact'),
    path('Marques/', views.Marques, name='Marques'),

    path('accessoire/', views.accessoire, name='accessoire'),
    path('ajouter-accessoire-panier/<int:accessoire_id>/', views.ajouter_accessoire_panier, name='ajouter_accessoire_panier'),

    path('favoris/toggle/<int:montre_id>/', views.toggle_favoris, name='toggle_favoris'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('mon-compte/historique/', views.historique_commandes, name='historique_commandes'),
    path('panier/retirer-accessoire/<int:ligne_id>/', views.retirer_accessoire_panier, name='retirer_accessoire_panier'),
    path('panier/modifier-quantite-accessoire/<int:ligne_id>/', views.modifier_quantite_accessoire, name='modifier_quantite_accessoire'),

    path('CGV/', views.CGV, name='CGV'),
    path('mentions-legales/', views.mentions_legales, name='mentions-legales'),
    path('confidentialite/', views.politique_confidentialite, name='confidentialite'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)