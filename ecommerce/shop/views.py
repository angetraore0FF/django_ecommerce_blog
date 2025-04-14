from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from shop.pdf_utils import generate_invoice_pdf
from .forms import CheckoutForm, CustomUserCreationForm
from .models import Commande, CustomUser, Collection, Favoris, LigneCommande, Montre, Marque, Panier, PanierItem, CodePromo
from .tokens import account_activation_token
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import CategorieAccessoire, Accessoire
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Accessoire, Panier, LignePanierAccessoire
from .forms import CommentaireForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            current_site = get_current_site(request)
            mail_subject = 'Activez votre compte'
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email = EmailMessage(mail_subject, message, to=[form.cleaned_data.get('email')])
            email.send()
            
            messages.success(request, 'Un lien d\'activation a été envoyé à votre adresse email.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inscription.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.save()
        login(request, user)
        messages.success(request, 'Votre compte a été activé avec succès!')
        return redirect('home')
    else:
        messages.error(request, 'Le lien d\'activation est invalide ou a expiré.')
        return redirect('home')

def home(request):
    return render(request, 'home.html')

def montres(request):
    montres = Montre.objects.filter(disponible=True).prefetch_related('images')
    return render(request, 'montres.html', {'montres': montres})


def detail_montre(request, montre_id):
    montre = get_object_or_404(
        Montre.objects.select_related('marque', 'collection').prefetch_related('images'), 
        pk=montre_id
    )
    commentaires = montre.commentaires.all().select_related('utilisateur')
    nouveau_commentaire = None
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentaireForm(data=request.POST)
        if form.is_valid():
            nouveau_commentaire = form.save(commit=False)
            nouveau_commentaire.montre = montre
            nouveau_commentaire.utilisateur = request.user
            nouveau_commentaire.save()
            messages.success(request, "Votre commentaire a été ajouté!")
            return redirect('detail_montre', montre_id=montre.id)
    else:
        form = CommentaireForm()
    
    return render(request, 'detail-montre.html', {
        'montre': montre,
        'commentaires': commentaires,
        'form': form,
        'nouveau_commentaire': nouveau_commentaire
    })

@login_required
def voir_panier(request):
    panier = get_object_or_404(Panier, utilisateur=request.user)
    return render(request, 'panier.html', {
        'panier': panier,
        'items_montres': panier.panier_items.all(),
        'items_accessoires': panier.lignes_accessoires.all()
    })

@login_required
def ajouter_au_panier(request, montre_id):
    montre = get_object_or_404(Montre, id=montre_id)
    
    if montre.stock <= 0:
        messages.error(request, "Désolé, cette montre n'est plus disponible en stock.")
        return redirect('montres')
    
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    
    panier_item, created = PanierItem.objects.get_or_create(
        panier=panier,
        montre=montre,
        defaults={'quantite': 1}
    )
    
    if not created and panier_item.quantite + 1 <= montre.stock:
        panier_item.quantite += 1
        panier_item.save()
    elif not created:
        messages.warning(request, "Quantité maximale disponible atteinte.")
    
    return redirect('voir_panier')

@login_required
def modifier_quantite(request, item_id):
    panier_item = get_object_or_404(PanierItem, id=item_id, panier__utilisateur=request.user)
    
    if request.method == 'POST':
        nouvelle_quantite = int(request.POST.get('quantite', 1))
        
        if nouvelle_quantite > panier_item.montre.stock:
            messages.warning(request, "Quantité demandée non disponible en stock.")
        elif nouvelle_quantite > 0:
            panier_item.quantite = nouvelle_quantite
            panier_item.save()
        else:
            panier_item.delete()
    
    return redirect('voir_panier')

@login_required
def retirer_du_panier(request, item_id):
    panier_item = get_object_or_404(PanierItem, id=item_id, panier__utilisateur=request.user)
    panier_item.delete()
    return redirect('voir_panier')

@login_required
def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login') + f"?next={request.path}"
    
    panier = get_object_or_404(Panier, utilisateur=request.user)
    code_promo = None
    reduction = 0
    
    if 'code_promo_id' in request.session:
        try:
            code_promo = CodePromo.objects.get(id=request.session['code_promo_id'])
            if not code_promo.est_valide():
                del request.session['code_promo_id']
                code_promo = None
            else:
                reduction = panier.total * code_promo.reduction / 100
        except CodePromo.DoesNotExist:
            del request.session['code_promo_id']
    
    total_avec_reduction = panier.total - reduction
    
    if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                # Vérification du stock
                for item in panier.panier_items.all():
                    if item.quantite > item.montre.stock:
                        messages.error(request, f"La montre {item.montre.nom} n'a plus assez de stock.")
                        return redirect('voir_panier')
                    
            
            # Construction de l'adresse
            adresse_livraison = f"{form.cleaned_data['nom']}\n{form.cleaned_data['adresse']}\n"
            adresse_livraison += f"{form.cleaned_data['code_postal']} {form.cleaned_data['ville']}\n"
            adresse_livraison += f"{form.cleaned_data['pays']}\nTél: {form.cleaned_data['telephone']}"
            
            # Création de la commande
            commande = Commande.objects.create(
                utilisateur=request.user,
                montant_total=total_avec_reduction,
                statut='PAYE',
                adresse_livraison=adresse_livraison,
                adresse_facturation=adresse_livraison,
                code_promo=code_promo
            )

            # Correction de l'indentation ici
            for item in panier.panier_items.all():
                if item.montre and item.montre.stock >= item.quantite:
                    LigneCommande.objects.create(
                        commande=commande,
                        montre=item.montre,
                        quantite=item.quantite,
                        prix_unitaire=item.montre.prix
                    )
                    # Mise à jour du stock
                    item.montre.stock -= item.quantite
                    if item.montre.stock <= 0:
                        item.montre.disponible = False
                    item.montre.save()

            for item in panier.lignes_accessoires.all():
                if item.accessoire and item.accessoire.stock >= item.quantite:
                    LigneCommande.objects.create(
                        commande=commande,
                        accessoire=item.accessoire,
                        quantite=item.quantite,
                        prix_unitaire=item.accessoire.prix
                    )
                    # Mise à jour du stock
                    item.accessoire.stock -= item.quantite
                    if item.accessoire.stock <= 0:
                        item.accessoire.en_stock = False
                    item.accessoire.save()

            # Vider le panier
            panier.panier_items.all().delete()
            panier.lignes_accessoires.all().delete()
            if 'code_promo_id' in request.session:
                del request.session['code_promo_id']

            # Générer le PDF
            pdf_buffer = generate_invoice_pdf(commande)
            
            # Envoyer l'email avec la facture en pièce jointe
            email = EmailMessage(
                f"Confirmation de commande #{commande.id}",
                render_to_string('email_confirmation_commande.txt', {'commande': commande}),
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
            )
            email.attach(
                f"facture_{commande.id}.pdf",
                pdf_buffer.getvalue(),
                'application/pdf'
            )
            email.send()

            return redirect('confirmation_commande', commande_id=commande.id)
    else:
        form = CheckoutForm()
    
    return render(request, 'checkout.html', {
        'panier': panier,
        'code_promo': code_promo,
        'reduction': reduction,
        'total_avec_reduction': total_avec_reduction,
        'items_montres': panier.panier_items.all(),
        'items_accessoires': panier.lignes_accessoires.all(),
        'form': form
    })

@login_required
def confirmation_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    if request.GET.get('download') == 'pdf':
        pdf_buffer = generate_invoice_pdf(commande)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_{commande.id}.pdf"'
        return response
    
    return render(request, 'confirmation.html', {'commande': commande})

@require_POST
@login_required
def appliquer_code_promo(request):
    code = request.POST.get('code', '').strip()
    if not code:
        return JsonResponse({'success': False, 'message': 'Veuillez entrer un code promo'})
    
    try:
        code_promo = CodePromo.objects.get(code__iexact=code)
        if not code_promo.est_valide():
            return JsonResponse({'success': False, 'message': 'Code promo invalide ou expiré'})
        
        request.session['code_promo_id'] = code_promo.id
        panier = get_object_or_404(Panier, utilisateur=request.user)
        reduction = panier.total * code_promo.reduction / 100
        
        return JsonResponse({
            'success': True,
            'code': code_promo.code,
            'reduction': float(reduction),
            'nouveau_total': float(panier.total - reduction)
        })
    except CodePromo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Code promo invalide'})

@login_required
def supprimer_code_promo(request):
    if 'code_promo_id' in request.session:
        del request.session['code_promo_id']
    return redirect('checkout')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        send_mail(
            f"Contact LuxuryTime: {subject}",
            f"Message de {name} ({email}):\n\n{message}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_EMAIL],
            fail_silently=False,
        )
        
        messages.success(request, "Votre message a bien été envoyé !")
        return redirect('contact')
    
    return render(request, 'contact.html')

def Marques(request):
    marques_data = [
        {
            'nom': 'Seiko Royal Oak',
            'description': 'Fondée en 1881, Seiko Royal Oak incarne l\'excellence horlogère japonaise...',
            'image': 'Seiko_royal_oak_or.png',
            'modeles': [
                {'nom': 'Royal Oak Chronograph', 'description': 'Mouvement automatique, boîtier or rose'},
                {'nom': 'Royal Oak Offshore', 'description': 'Édition limitée, cadran bleu'},
            ]
        },
        {
            'nom': 'Seiko Oyster',
            'description': 'La légendaire maison Seiko Oyster, fondée en 1905...',
            'image': 'Seiko_oyster_perpetual_bleu.png',
            'modeles': [
                {'nom': 'Oyster Perpetual', 'description': 'Cadran bleu, acier inoxydable'},
            ]
        },
    ]
    
    context = {
        'marques': marques_data,
    }
    
    return render(request, 'Marques.html', context)

def accessoire(request):
    categories = CategorieAccessoire.objects.all().prefetch_related('accessoires')
    accessoires_phares = Accessoire.objects.filter(en_stock=True).order_by('?')[:4]
    
    context = {
        'categories': categories,
        'accessoires_phares': accessoires_phares,
    }
    return render(request, 'accessoire.html', context)

@login_required
def ajouter_accessoire_panier(request, accessoire_id):
    accessoire = get_object_or_404(Accessoire, id=accessoire_id)
    
    if accessoire.stock <= 0:
        messages.error(request, "Cet accessoire n'est plus disponible en stock.")
        return redirect('accessoire')
    
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    
    ligne_panier, created = LignePanierAccessoire.objects.get_or_create(
        panier=panier,
        accessoire=accessoire,
        defaults={'quantite': 1}
    )
    
    if not created:
        if ligne_panier.quantite + 1 <= accessoire.stock:
            ligne_panier.quantite += 1
            ligne_panier.save()
        else:
            messages.warning(request, "Quantité maximale disponible atteinte pour cet accessoire.")
    
    messages.success(request, f"{accessoire.nom} a été ajouté à votre panier")
    return redirect('accessoire')

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else reverse_lazy('home')

@login_required
def toggle_favoris(request, montre_id):
    montre = get_object_or_404(Montre, id=montre_id)
    favori, created = Favoris.objects.get_or_create(
        utilisateur=request.user,
        montre=montre
    )
    
    if not created:
        favori.delete()
        return JsonResponse({'status': 'removed', 'message': 'Montre retirée des favoris'})
    
    return JsonResponse({'status': 'added', 'message': 'Montre ajoutée aux favoris'})

@login_required
def mes_favoris(request):
    favoris = request.user.favoris.select_related('montre', 'montre__marque').prefetch_related('montre__images')
    return render(request, 'mes_favoris.html', {'favoris': favoris})

@login_required
def historique_commandes(request):
    commandes = request.user.commandes.select_related('code_promo').prefetch_related('lignes').order_by('-date_commande')
    return render(request, 'historique_commandes.html', {'commandes': commandes})

@login_required
@require_POST
def retirer_accessoire_panier(request, ligne_id):
    ligne = get_object_or_404(LignePanierAccessoire, id=ligne_id, panier__utilisateur=request.user)
    ligne.delete()
    messages.success(request, "L'accessoire a été retiré de votre panier")
    return redirect('voir_panier')

@login_required
def modifier_quantite_accessoire(request, ligne_id):
    ligne = get_object_or_404(LignePanierAccessoire, id=ligne_id, panier__utilisateur=request.user)
    
    if request.method == 'POST':
        nouvelle_quantite = int(request.POST.get('quantite', 1))
        
        if nouvelle_quantite > ligne.accessoire.stock:
            messages.warning(request, "Quantité demandée non disponible en stock.")
        elif nouvelle_quantite > 0:
            ligne.quantite = nouvelle_quantite
            ligne.save()
        else:
            ligne.delete()
    
    return redirect('voir_panier')

def CGV(request):
    return render(request, 'CGV.html')

def mentions_legales(request):
    return render(request, 'mentions.html')

def politique_confidentialite(request):
    return render(request, 'confidentialite.html')