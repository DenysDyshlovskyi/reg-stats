from django.shortcuts import render
from django.conf import settings
from .models import Clients, DataBackup
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

# Renders in the index page, or default page
def index(request):
    # Get all clients
    clients = []
    for client in Clients.objects.all():
        dict = {}
        dict["nickname"] = client.nickname
        dict["id"] = str(client.id)
        pc_info = json.loads(client.pc_info)
        for key in pc_info:
            dict[key] = pc_info[key]
        clients.append(dict)
    context = importStaticFiles("index")

    # Get startup data
    list = []
    for row in DataBackup.objects.all():
        list.append(row.data)

    context["startup_data"] = json.dumps(list)
    context["clients"] = clients
    context["clients_info_json"] = json.dumps(clients)
    return render(request, "index.html", context)