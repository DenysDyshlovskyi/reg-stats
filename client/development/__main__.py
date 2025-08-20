import requests
import websockets
import asyncio
import os
import json
import time
import subprocess
import datetime
import traceback

def main():
    # Define variables
    DEBUG = True
    DEBUG_FILE_PATH = os.path.join(os.getcwd(), "debug.txt")
    WEBSOCKET_PREFIX = "ws://"
    HTTP_PREFIX = "http://"
    CPU_SEND_INTERVAL = 1
    RAM_SEND_INTERVAL = 1

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

                # Gets cpu usage and sends it
                async def send_cpu(websocket):
                    while True:
                        try:
                            # Get cpu percentage
                            command = "wmic cpu get loadpercentage"
                            cpu_percent = subprocess.check_output(command, shell=True).decode().strip().split('\n')[1]
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'cpu_percent',
                                'percent': cpu_percent,
                                'client_id': client_id
                            }))
                            await asyncio.sleep(CPU_SEND_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(CPU_SEND_INTERVAL)

                # Gets ram usage and sends it
                async def send_ram(websocket):
                    while True:
                        try:
                            # Get ram usage
                            command = "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory"
                            ram_info = subprocess.check_output(command, shell=True).decode().strip().split('\n')[1]
                            free_ram, total_ram = map(int, ram_info.split())
                            used_ram = (total_ram - free_ram)
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'ram_usage',
                                'total_gb': round(((total_ram / 1024) / 1024), 1),
                                'usage_gb': round(((used_ram / 1024) / 1024), 1),
                                'client_id': client_id
                            }))
                            await asyncio.sleep(RAM_SEND_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(RAM_SEND_INTERVAL)

                async with websockets.connect(uri, additional_headers=headers) as websocket:
                    # Start cpu and ram tasks as background processes
                    cpu_send_task = asyncio.create_task(send_cpu(websocket=websocket))
                    ram_send_task = asyncio.create_task(send_ram(websocket=websocket))
                    while True:
                        # Wait for messages from websocket
                        try:
                            response = await websocket.recv()
                            write_to_debug(f"Response received: {response}")
                        except Exception:
                            write_to_debug(f"Failed receiving responses: {traceback.format_exc()}")
                            if cpu_send_task:
                                cpu_send_task.cancel()
                                ram_send_task.cancel()
                            await asyncio.sleep(1)
                            break

            try:
                asyncio.run(connect())
            except Exception:
                write_to_debug(f"Error connecting to websocket: {traceback.format_exc()}")
                time.sleep(10)
        except Exception as e:
            write_to_debug(traceback.format_exc())
            time.sleep(10)

if __name__ == '__main__':
    main()