from django.contrib import admin
from .models import CodePromo, Commande, Favoris, LigneCommande, Montre, Marque, ImageMontre
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import CategorieAccessoire, Accessoire
from .models import Commentaire


class ImageMontreInline(admin.TabularInline):
    model = ImageMontre
    extra = 3  # Nombre de champs d'upload d'images affichés
    fields = ('image', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;"/>'
        return "Aucune image"
    image_preview.allow_tags = True

@admin.register(Montre)
class MontreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'marque', 'prix', 'disponible', 'stock','mouvement')
    list_filter = ('marque', 'disponible', 'mouvement')
    search_fields = ('nom', 'description')
    list_editable = ('stock', 'disponible')
    inlines = [ImageMontreInline]
    fieldsets = (
        (None, {
            'fields': ('nom', 'description', 'prix')
        }),
        ('Détails', {
            'fields': ('marque', 'genre', 'mouvement', 'stock', 'disponible')  
        }),
    )
    def en_stock(self, obj):
        return obj.stock > 0
    en_stock.boolean = True
    en_stock.short_description = 'En stock'

admin.site.register(Marque)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'is_active', 'email_verified', 'is_staff')
    list_filter = ('is_active', 'email_verified', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'email_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(CodePromo)
class CodePromoAdmin(admin.ModelAdmin):
    list_display = ('code', 'reduction', 'date_debut', 'date_fin', 'actif', 'utilisations', 'utilisations_max')
    list_filter = ('actif',)
    search_fields = ('code',)

@admin.register(CategorieAccessoire)
class CategorieAccessoireAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Accessoire)
class AccessoireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'marque', 'prix', 'en_stock', 'stock')
    list_filter = ('categorie', 'en_stock')
    search_fields = ('nom', 'marque')


@admin.register(Favoris)
class FavorisAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'montre', 'date_ajout')
    list_filter = ('utilisateur', 'date_ajout')
    search_fields = ('utilisateur__email', 'montre__nom')

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'date_commande', 'montant_total', 'statut')
    list_filter = ('statut', 'date_commande')
    search_fields = ('utilisateur__email', 'id')
    inlines = [LigneCommandeInline]

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'montre', 'date_creation', 'note')
    list_filter = ('date_creation', 'note')
    search_fields = ('utilisateur__email', 'montre__nom', 'texte')