from django.shortcuts import render
from django.conf import settings
from .models import Clients, DataBackup, ClientConnectionStatus
from django.http import JsonResponse
import json
import os

# Create your views here.
static_dir = os.path.join(settings.BASE_DIR, 'static')

# Function for loading in static js and css files as plain text
def importStaticFiles(name):
    context = {}

    # universal files
    with open(os.path.join(static_dir, 'css', 'universal.css'), 'r') as file:
        context["universal_css"] = file.read()
    with open(os.path.join(static_dir, 'js', 'universal.js'), 'r') as file:
        context["universal_js"] = file.read()

    # Specific files
    with open(os.path.join(static_dir, 'css', f'{name}.css'), 'r') as file:
        context[f"{name}_css"] = file.read()
    with open(os.path.join(static_dir, 'js', f'{name}.js'), 'r') as file:
        context[f"{name}_js"] = file.read()

    return context

# Wipes all chart data and online offline data
def wipedata(request):
    DataBackup.objects.all().delete()
    ClientConnectionStatus.objects.all().delete()
    Clients.objects.all().delete()
    return JsonResponse({
        "success": {
            "code": "OK"
        }
    }, status=200)

# Renders in the index page, or default page
def index(request):
    # Check password
    password = request.COOKIES.get('regstats-password')
    if not password:
        return JsonResponse({
            "error": {
                "code": "UNAUTHORIZED"
            }
        }, status=401)

    if password != settings.WHITELIST_PASSWORD:
        return JsonResponse({
            "error": {
                "code": "UNAUTHORIZED"
            }
        }, status=401)
    # Define section ids
    section_ids = []

    # Get all clients
    clients = []
    for client in Clients.objects.all():
        dict = {}
        dict["nickname"] = client.nickname
        dict["id"] = str(client.id)
        if ClientConnectionStatus.objects.filter(client_id=client.id).exists():
            connection_row = ClientConnectionStatus.objects.get(client_id=client)
            if connection_row.status:
                dict["online"] = True
            else:
                dict["online"] = False
            dict["last_online"] = connection_row.unix_timestamp
        else:
            dict["online"] = False
            dict["last_online"] = 0
        pc_info = json.loads(client.pc_info)
        for key in pc_info:
            dict[key] = pc_info[key]
        clients.append(dict)
        section_ids.append(f"{client.id}-slide")
        section_ids.append(f"{client.id}-slide2")
    context = importStaticFiles("index")

    # Get startup data
    list = []
    for row in DataBackup.objects.all():
        list.append(row.data)

    context["startup_data"] = json.dumps(list)
    context["clients"] = clients
    context["clients_info_json"] = json.dumps(clients)
    context["section_ids"] = json.dumps(section_ids)

    # Get chart js
    with open(os.path.join(static_dir, 'js', 'chart.js'), 'r') as file:
        context["chart_js"] = file.read()

    return render(request, "index.html", context)

def add_password(request):
    return render(request, "add_password.html")

def change_nickname(request):
    # Check password
    password = request.COOKIES.get('regstats-password')
    if not password:
        return JsonResponse({
            "error": {
                "code": "UNAUTHORIZED"
            }
        }, status=401)

    if password != settings.WHITELIST_PASSWORD:
        return JsonResponse({
            "error": {
                "code": "UNAUTHORIZED"
            }
        }, status=401)

    context = {
        "clients": Clients.objects.all()
    }
    return render(request, "change_nickname.html", context)