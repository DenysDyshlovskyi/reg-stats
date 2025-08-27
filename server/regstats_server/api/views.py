# All views for paths starting with /api/
from django.http import JsonResponse, StreamingHttpResponse
from ..models import Clients, DataBackup
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import re
import os

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
        
        # Parse pcinfo
        pc_info = json.loads(body["pcInfo"])

        # Generate client uuid
        client_id = uuid.uuid4()

        # Insert client into database
        client = Clients(
            id=client_id,
            nickname=pc_info["username"],
            pc_info=json.dumps(pc_info)
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

# Check if a newer update exists and responds with it
@csrf_exempt
def get_update(request):
    if request.method == "POST":
        body = json.loads(request.body)
        master_key = body["masterKey"]
        client_id = body["clientId"]
        current_version = body["currentVersion"]

        if not client_id or not master_key or not current_version:
            return JsonResponse({
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "POST request is missing three keys: client_id, master_key and current_version"
                }
            }, status=400)

        # Check if client exists
        if not Clients.objects.filter(id=client_id).exists():
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Client does not exist or is deleted."
                }
            }, status = 404)

        # Check if an update exists
        update_files = os.listdir(settings.UPDATES_ROOT)
        if not update_files:
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "No update found."
                }
            }, status=404)

        # Find the latest update file
        latest_update = max(update_files, key=lambda x: int(x.split('-')[1].replace('.zip', '')))
        update_file_path = os.path.join(settings.UPDATES_ROOT, latest_update)

        # Get update version
        file_name = os.path.basename(update_file_path)
        match = re.search(r'update-(\d+)\.zip', file_name)
        if match:
            update_version = match.group(1)  # Extract the matched number
        else:
            return JsonResponse({
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Something went wrong."
                }
            }, status=500)

        # Check if this version is higher than the current version
        if int(update_version) > int(current_version):
            # Stream the file to handle async correctly
            try:
                def file_iterator(file_path, chunk_size=8192):
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(chunk_size):
                            yield chunk

                response = StreamingHttpResponse(file_iterator(update_file_path))
                response['Content-Type'] = 'application/octet-stream'
                response['Content-Disposition'] = f'attachment; filename={latest_update}'
                return response
            except Exception as e:
                return JsonResponse({
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": f"Error opening update file: {str(e)}"
                    }
                }, status=500)
        else:
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "No new update found. You are on the latest version."
                }
            }, status=404)
    else:
        return JsonResponse({
            "error": {
                "code": "NOT_ALLOWED",
                "message": "Method not Allowed. Allowed: POST"
            }
        }, status=405)

# Backs up data to database
@csrf_exempt
def add_data(request):
    if request.method == "POST":
        body = json.loads(request.body)
        master_key = body["master_key"]
        data_dict = body["data_dict"]

        # Check if body is empty
        if not data_dict or not master_key:
            return JsonResponse({
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "POST request is missing two keys: master_key and data_dict"
                }
            }, status=400)

        # Get client id
        client_id = data_dict["client_id"]

        # Check if client exists
        if not Clients.objects.filter(id=client_id).exists():
            return JsonResponse({
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Client does not exist or is deleted."
                }
            }, status = 404)

        client = Clients.objects.get(id=client_id)

        # Insert into database
        row = DataBackup(
            client_id=client,
            type=data_dict["type"],
            data = json.dumps(data_dict)
        )
        row.save()

        newest = DataBackup.objects.filter(client_id=client_id, type=data_dict["type"]).order_by("-id")[:10]
        for row in DataBackup.objects.filter(client_id=client_id, type=data_dict["type"]):
            if row not in newest:
                row.delete()

        return JsonResponse({
            "CODE": "OK"
        }, status=201)
    else:
        return JsonResponse({
            "error": {
                "code": "NOT_ALLOWED",
                "message": "Method not Allowed. Allowed: POST"
            }
        }, status=405)