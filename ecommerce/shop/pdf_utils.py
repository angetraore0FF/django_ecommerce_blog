from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from .models import Commande

def generate_invoice_pdf(commande):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Contenu du PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    elements.append(Paragraph("Facture LuxuryTime", styles['Title']))
    
    # Informations de la commande
    elements.append(Paragraph(f"<b>Commande #</b> {commande.id}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {commande.date_commande.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Client:</b> {commande.utilisateur.email}", styles['Normal']))
    
    # Lignes de commande
    data = [['Produit', 'Quantité', 'Prix unitaire', 'Total']]
    for ligne in commande.lignes.all():
        produit = ligne.montre if ligne.montre else ligne.accessoire
        data.append([
            produit.nom,
            str(ligne.quantite),
            f"{ligne.prix_unitaire} €",
            f"{ligne.total_ligne} €"
        ])
    
    # Tableau des produits
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t)
    
    # Total
    elements.append(Paragraph(f"<b>Total:</b> {commande.montant_total} €", styles['Normal']))
    
    # Génération du PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer