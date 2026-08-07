from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from jsonschema import ValidationError


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    email_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Collection(models.Model):  # Ajout du modèle manquant
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom

class Marque(models.Model):
    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='marques/')

    def __str__(self):
        return self.nom

class Montre(models.Model):
    GENRE_CHOICES = [
        ('H', 'Homme'),
        ('F', 'Femme'),
        ('U', 'Unisexe'),
    ]
    MOUVEMENT_CHOICES = [
        ('AUTO', 'Automatique'),
        ('QUARTZ', 'Quartz'),
        ('MECA', 'Mécanique'),
        ('SMART', 'Smartwatch'),
    ]
    
    mouvement = models.CharField(
        max_length=10,
        choices=MOUVEMENT_CHOICES,
        default='QUARTZ',
        verbose_name="Type de mouvement"
    )
    
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES)
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True)
    disponible = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)  # Nouveau champ pour le stock
    
    def __str__(self):
        return f"{self.marque} {self.nom}"
    
    @property
    def en_stock(self):
        """Retourne True si le produit est en stock"""
        return self.stock > 0

class ImageMontre(models.Model):
    montre = models.ForeignKey(Montre, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='montres/')  # Remplacez CharField par ImageField
    ordre = models.PositiveIntegerField(default=0)
    

User = get_user_model()

class Panier(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        total_montres = sum(item.sous_total for item in self.panier_items.all())
        total_accessoires = sum(item.sous_total for item in self.lignes_accessoires.all())
        return total_montres + total_accessoires

class PanierItem(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='panier_items')
    montre = models.ForeignKey('Montre', on_delete=models.CASCADE, related_name='panier_items')
    quantite = models.PositiveIntegerField(default=1)

    @property
    def sous_total(self):
        return self.montre.prix * self.quantite
    
class CodePromo(models.Model):
    code = models.CharField(max_length=20, unique=True)
    reduction = models.DecimalField(max_digits=5, decimal_places=2)  # En pourcentage ou montant fixe
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    actif = models.BooleanField(default=True)
    utilisations_max = models.PositiveIntegerField(default=1)
    utilisations = models.PositiveIntegerField(default=0)

    def est_valide(self):
        now = timezone.now()
        return (self.actif and 
                self.date_debut <= now <= self.date_fin and
                self.utilisations < self.utilisations_max)

    def __str__(self):
        return f"{self.code} (-{self.reduction}%)"

class Commande(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYE', 'Payée'),
        ('EXPEDIEE', 'Expédiée'),
        ('LIVREE', 'Livrée'),
        ('ANNULEE', 'Annulée'),
    ]

    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='commandes')
    date_commande = models.DateTimeField(auto_now_add=True)
    code_promo = models.ForeignKey(CodePromo, null=True, blank=True, on_delete=models.SET_NULL)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    adresse_livraison = models.TextField(null=True, blank=True, max_length=255)
    adresse_facturation = models.TextField(null=True, blank=True, max_length=255)
    methode_paiement = models.CharField(null=True, blank=True, max_length=150)

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.email}"

class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    montre = models.ForeignKey(Montre, on_delete=models.SET_NULL, null=True, blank=True)
    accessoire = models.ForeignKey('Accessoire', on_delete=models.SET_NULL, null=True, blank=True)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if not self.montre and not self.accessoire:
            raise ValidationError("Une ligne de commande doit avoir au moins un produit (montre ou accessoire)")
        if self.montre and self.accessoire:
            raise ValidationError("Une ligne de commande ne peut pas avoir à la fois une montre et un accessoire")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def get_nom_produit(self):
        if self.montre:
            return self.montre.nom
        elif self.accessoire:
            return self.accessoire.nom
        return "Produit non spécifié"

    @property
    def total_ligne(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        if self.montre:
            return f"{self.montre.nom} x {self.quantite}"
        elif self.accessoire:
            return f"{self.accessoire.nom} x {self.quantite}"
        return f"Ligne de commande #{self.id}"

class CategorieAccessoire(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='categories_accessoires/')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom

class Accessoire(models.Model):
    categorie = models.ForeignKey(CategorieAccessoire, on_delete=models.CASCADE, related_name='accessoires')
    nom = models.CharField(max_length=200)
    marque = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='accessoires/')
    en_stock = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.marque} - {self.nom}"
    
class Favoris(models.Model):
    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favoris')
    montre = models.ForeignKey(Montre, on_delete=models.CASCADE)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'montre')
        verbose_name_plural = 'Favoris'

    def __str__(self):
        return f"{self.utilisateur.email} - {self.montre.nom}"
    
class LignePanierAccessoire(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='lignes_accessoires')
    accessoire = models.ForeignKey('Accessoire', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

    @property
    def sous_total(self):
        return self.accessoire.prix * self.quantite

# Dans models.py, ajoutez ce code en haut du fichier

@receiver(post_save, sender=CustomUser)
def create_user_panier(sender, instance, created, **kwargs):
    if created:
        Panier.objects.create(utilisateur=instance)

class Commentaire(models.Model):
    montre = models.ForeignKey(Montre, on_delete=models.CASCADE, related_name='commentaires')
    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    texte = models.TextField(max_length=500)
    date_creation = models.DateTimeField(auto_now_add=True)
    note = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],  # Notes de 1 à 5
        null=True, 
        blank=True
    )

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Commentaire de {self.utilisateur.email} sur {self.montre.nom}"