from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from shop.models import Commentaire

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    username = forms.CharField(
        label=_("Username"),
        required=False,
        help_text=_("Optional.")
    )

    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['texte', 'note']
        widgets = {
            'texte': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'note': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'texte': 'Votre commentaire',
            'note': 'Note (facultative)'
        }

# Dans forms.py
from django import forms

class CheckoutForm(forms.Form):
    nom = forms.CharField(label='Nom complet', max_length=100)
    adresse = forms.CharField(label='Adresse', widget=forms.Textarea)
    ville = forms.CharField(label='Ville', max_length=100)
    code_postal = forms.CharField(label='Code postal', max_length=20)
    pays = forms.CharField(label='Pays', max_length=100)
    email = forms.EmailField(label='Email')
    telephone = forms.CharField(label='Téléphone', max_length=20)
    carte = forms.CharField(label='Numéro de carte', max_length=16)
    expiration = forms.CharField(label='Date d\'expiration', max_length=5)
    cvv = forms.CharField(label='CVV', max_length=3)