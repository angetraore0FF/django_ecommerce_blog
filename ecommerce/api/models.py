from django.db import models
from shop.models import Montre, Accessoire, CustomUser  # Importez depuis votre app principale

class ProductReview(models.Model):
    """Modèle pour les avis sur les produits"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    montre = models.ForeignKey(Montre, on_delete=models.CASCADE, null=True, blank=True)
    accessoire = models.ForeignKey(Accessoire, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(montre__isnull=False) | models.Q(accessoire__isnull=False),
                name='at_least_one_product_type'
            )
        ]

    def __str__(self):
        return f"Avis {self.rating}★ par {self.user.email}"