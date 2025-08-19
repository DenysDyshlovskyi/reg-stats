import requests
import websockets
import asyncio
import os
import json
import time
import datetime

def main():
    # Define variables
    DEBUG = True
    DEBUG_FILE_PATH = os.path.join(os.getcwd(), "debug.txt")

    # Create debug text file if it doesnt exist
    if not os.path.exists(DEBUG_FILE_PATH):
        with open(DEBUG_FILE_PATH, "w") as f:
            pass

    # Writes something to debug file
    def write_to_debug(e):
        if DEBUG:
            with open(DEBUG_FILE_PATH, 'a') as debug_file:
                ct = datetime.datetime.now()
                debug_file.write(f"-------------------- {ct} -------------------- \n {str(e)} \n")
            debug_file.close()

    while True:
        try:
            # Import variables
            with open(os.path.join(os.getcwd(), "vars.json"), "r") as file:
                vars = json.loads(file.read())
                file.close()

            # Define variables
            client_id = vars["client_id"]
            master_key = vars["master_key"]
            domain_http = vars["domain_http"]

            # Generate session for client
            session = requests.Session()
            session.post(f"http://{domain_http}/api/get_ws_session", data={
                "client_id": client_id,
                "master_key": master_key
            })

            # Get session id from cookies
            cookies = session.cookies.get_dict()
            sessionid = cookies.get('sessionid')

            # Use sessionid in websocket headers
            async def connect():
                uri = f"ws://{domain_http}/ws/client/"
                headers = {
                    'Cookie': f'sessionid={sessionid}'
                }

                async with websockets.connect(uri, extra_headers=headers) as websocket:
                    await websocket.send({
                        'sender': 'c',
                        'type': 'test',
                        'client_id': client_id
                    })

            asyncio.run(connect())
        except Exception as e:
            write_to_debug(e)
            time.sleep(10)

if __name__ == '__main__':
    main()