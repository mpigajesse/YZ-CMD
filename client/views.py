from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Client

# Create your views here.

@login_required
def liste_clients(request):
    clients = Client.objects.all()
    search_query = request.GET.get('search', '')

    if search_query:
        clients = clients.filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(numero_tel__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(adresse__icontains=search_query)
        )

    clients = clients.order_by('-date_creation')

    paginator = Paginator(clients, 10)  # 10 clients par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_clients': Client.objects.count(),
    }
    return render(request, 'client/liste_clients.html', context)

@login_required
def detail_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    context = {
        'client': client
    }
    return render(request, 'client/detail_client.html', context)

@login_required
def creer_client(request):
    if request.method == 'POST':
        numero_tel = request.POST.get('numero_tel')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')

        if not numero_tel:
            messages.error(request, "Le numéro de téléphone est obligatoire.")
        elif Client.objects.filter(numero_tel=numero_tel).exists():
            messages.error(request, f"Un client avec le numéro {numero_tel} existe déjà.")
        else:
            Client.objects.create(
                numero_tel=numero_tel,
                nom=nom,
                prenom=prenom,
                email=email,
                adresse=adresse
            )
            messages.success(request, "Client créé avec succès.")
            return redirect('client:liste')

    return render(request, 'client/creer_client.html')

@login_required
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.numero_tel = request.POST.get('numero_tel')
        client.nom = request.POST.get('nom')
        client.prenom = request.POST.get('prenom')
        client.email = request.POST.get('email')
        client.adresse = request.POST.get('adresse')

        # Vérifier si le numéro de téléphone est déjà pris par un autre client
        if Client.objects.filter(numero_tel=client.numero_tel).exclude(pk=client.pk).exists():
            messages.error(request, f"Un autre client utilise déjà le numéro {client.numero_tel}.")
        else:
            client.save()
            messages.success(request, "Client modifié avec succès.")
            return redirect('client:detail', pk=client.pk)

    context = {
        'client': client
    }
    return render(request, 'client/modifier_client.html', context)

@login_required
def supprimer_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, "Client supprimé avec succès.")
        return redirect('client:liste')
    
    # Pour la modale de confirmation, on pourrait rendre un template simple ou gérer via JS
    return render(request, 'composant_generale/modal_confirmation_suppression.html', {
        'item_id': pk,
        'item_name': f"Client {client.get_full_name()}",
        'delete_url': request.path, # L'URL de suppression est la page actuelle
        'redirect_url': '/client/liste/',
    })

@require_POST
@login_required
def supprimer_clients_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun client sélectionné pour la suppression.")
        return redirect('client:liste')

    try:
        count = Client.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} client(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('client:liste')
