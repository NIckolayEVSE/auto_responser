from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def statistics(request):
    template = 'statistics/index.html'

    context = {
        'products_in_work': 0,
        'client_with_subscribe': 0,
        'count_clients': 0,
        'count_chats': 0,
        'count_clients_week': 0,
        'count_clients_today': 0,
        'count_clients_months': 0,
    }

    return render(request, template, context)
