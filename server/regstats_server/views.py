from django.shortcuts import render
from django.conf import settings
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
    context = importStaticFiles("index")
    return render(request, "index.html", context)