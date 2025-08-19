# All views for paths starting with /api/
from django.http import JsonResponse
from ..models import Clients
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

# Endpoint for registering client in database
@csrf_exempt
def register(request):
    if request.method == "POST":
        # Get post data
        body = json.loads(request.body)
        master_key = body["masterKey"]

        # Check if master key matches
        if master_key != settings.MASTER_KEY:
            return JsonResponse({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Incorrect master key."
                }
            }, status=401)

        # Get client details
        username = body["username"]
        domain = body["domain"]
        computer_name = body["computerName"]

        # Generate client uuid
        client_id = uuid.uuid4()

        # Insert client into database
        client = Clients(
            id=client_id,
            username=username,
            domain=domain,
            computer_name=computer_name
        )
        client.save()

        # Return client id
        return JsonResponse({
            "code": "OK",
            "client_id": str(client_id)
        }, status=201)
    else:
        return JsonResponse({
            "error": {
                "code": "NOT_ALLOWED",
                "message": "Method not Allowed. Allowed: POST"
            }
        }, status=405)

# Endpoint for removing client from database
@csrf_exempt
def remove_client(request):
    if request.method == "POST":
        # Get post data
        body = json.loads(request.body)
        master_key = body["masterKey"]

        # Check if master key matches
        if master_key != settings.MASTER_KEY:
            return JsonResponse({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Incorrect master key."
                }
            }, status=401)

        # Get client id
        client_id = body["clientId"]

        # Check if client exists
        if not Clients.objects.filter(id=client_id).exists():
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Client does not exist or is already deleted."
                }
            }, status = 404)

        # Delete client from database
        Clients.objects.get(id=client_id).delete()

        # Return
        return JsonResponse({
            "code": "OK"
        }, status=200)
    else:
        return JsonResponse({
            "error": {
                "code": "NOT_ALLOWED",
                "message": "Method not Allowed. Allowed: POST"
            }
        }, status=405)

# Gets a session id to use to connect to websocket
@csrf_exempt
def get_ws_session(request):
    if request.method == "POST":
        # Get post data
        client_id = request.POST.get("client_id")
        master_key = request.POST.get("master_key")

        # Check if values are empty
        if not client_id or not master_key:
            return JsonResponse({
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "POST request is missing two keys: client_id and master_key"
                }
            }, status=400)

        # Check if master key matches
        if master_key != settings.MASTER_KEY:
            return JsonResponse({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Incorrect master key."
                }
            }, status=401)

        # Check if client exists
        if not Clients.objects.filter(id=client_id).exists():
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Client does not exist or is deleted."
                }
            }, status = 404)

        # Get client instance
        client = Clients.objects.get(id=client_id)

        # Save client id and master key to session
        uuid_str = str(client.id)
        request.session['client_id'] = uuid_str
        request.session['master_key'] = master_key

        # Return
        return JsonResponse({
            "code": "OK"
        }, status=200)
    else:
        return JsonResponse({
            "error": {
                "code": "NOT_ALLOWED",
                "message": "Method not Allowed. Allowed: POST"
            }
        }, status=405)