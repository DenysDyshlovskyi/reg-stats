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
    WEBSOCKET_PREFIX = "ws://"
    HTTP_PREFIX = "http://"

    # Create debug text file if it doesnt exist
    if not os.path.exists(DEBUG_FILE_PATH):
        with open(DEBUG_FILE_PATH, "w") as f:
            pass

    # Writes something to debug file
    def write_to_debug(e):
        if DEBUG:
            print(e)
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
            response = session.post(f"{HTTP_PREFIX}{domain_http}/api/get_ws_session", data={
                "client_id": client_id,
                "master_key": master_key
            })
            write_to_debug(response)

            # Get session id from cookies
            cookies = session.cookies.get_dict()
            sessionid = cookies.get('sessionid')
            write_to_debug(f"Session id: {sessionid}")

            # Use sessionid in websocket headers
            async def connect():
                uri = f"{WEBSOCKET_PREFIX}{domain_http}/ws/client/"
                write_to_debug(f"Websocket url: {uri}")
                headers = {
                    'Cookie': f'sessionid={sessionid}',
                    'Origin': f'{HTTP_PREFIX}{domain_http}'
                }

                async with websockets.connect(uri, additional_headers=headers) as websocket:
                    while True:
                        try:
                            response = await websocket.recv()
                            write_to_debug(f"Response received: {response}")
                        except Exception as e:
                            write_to_debug(e)
                            break
            try:
                asyncio.run(connect())
            except Exception as e:
                write_to_debug(f"Error connecting to websocket: {e}")
        except Exception as e:
            write_to_debug(e)
            time.sleep(10)

if __name__ == '__main__':
    main()