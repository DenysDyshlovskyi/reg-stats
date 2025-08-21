import requests
import websockets
import asyncio
import os
import json
import time
import subprocess
import datetime
import traceback
import re

def main():
    # Define variables
    DEBUG = True
    DEBUG_FILE_PATH = os.path.join(os.getcwd(), "debug.txt")
    WEBSOCKET_PREFIX = "ws://"
    HTTP_PREFIX = "http://"
    CPU_SEND_INTERVAL = 1
    RAM_SEND_INTERVAL = 1
    PING_INTERVAL = 1
    BANDWIDTH_INTERVAL = 1
    BANDWIDTH_SEND_DELAY = 5

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

                # Gets ping in ms
                async def ping(websocket):
                    while True:
                        try:
                            # Remove port from domain_http if it exists
                            if ":" in domain_http:
                                ping_target = domain_http.split(":")[0]
                            else:
                                ping_target = domain_http

                            # Run the ping command asynchronously
                            process = await asyncio.create_subprocess_exec(
                                "ping", "-n", "1", ping_target, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                            )

                            # Capture the output
                            stdout, stderr = await process.communicate()

                            # Decode the output to string
                            ping_output = stdout.decode()

                            # Use regex to find the time value
                            match = re.search(r"time[=<](\d+ms)", ping_output)
                            if match:
                                ping = match.group(1)
                                await websocket.send(json.dumps({
                                    'sender': 'c',
                                    'type': 'ping',
                                    'ping': ping,
                                    'client_id': client_id
                                }))
                            else:
                                write_to_debug(f"Error getting ping: {ping_output}")
                            await asyncio.sleep(PING_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(PING_INTERVAL)

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

                async def get_netstat_stats():
                    # Run netstat command to get network stats
                    process = await asyncio.create_subprocess_exec(
                        "netstat", "-e", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    return stdout.decode()

                def parse_netstat_stats(output):
                    # Regex to extract the Received and Sent bytes from the correct row
                    received_bytes, sent_bytes = 0, 0
                    lines = output.splitlines()
                    
                    # Look for the line that contains "Bytes" in the second row after the header
                    for line in lines:
                        # Match the line with the format of the row containing bytes
                        match = re.search(r"\s*(\d+)\s+(\d+)", line)
                        if match:
                            received_bytes = int(match.group(1))  # Received bytes
                            sent_bytes = int(match.group(2))      # Sent bytes
                            break

                    return received_bytes, sent_bytes

                async def measure_bandwidth():
                    # Record initial stats
                    initial_output = await get_netstat_stats()
                    initial_stats = parse_netstat_stats(initial_output)

                    await asyncio.sleep(BANDWIDTH_INTERVAL)

                    # Record stats after interval
                    final_output = await get_netstat_stats()
                    final_stats = parse_netstat_stats(final_output)

                    # Calculate bandwidth usage
                    received_bandwidth = (final_stats[0] - initial_stats[0]) / BANDWIDTH_INTERVAL
                    transmitted_bandwidth = (final_stats[1] - initial_stats[1]) / BANDWIDTH_INTERVAL

                    return received_bandwidth, transmitted_bandwidth

                # Sends bandwidth to websocket
                async def get_bandwidth(websocket):
                    while True:
                        try:
                            # Get bandwidth from other function
                            received_bandwidth, transmitted_bandwidth = await measure_bandwidth()

                            # Send through websocket
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'bandwidth',
                                'received': received_bandwidth,
                                'transmitted': transmitted_bandwidth,
                                'bandwidth_interval': BANDWIDTH_INTERVAL,
                                'client_id': client_id
                            }))

                            await asyncio.sleep(BANDWIDTH_SEND_DELAY)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(BANDWIDTH_SEND_DELAY)

                async with websockets.connect(uri, additional_headers=headers) as websocket:
                    # Start cpu, ping and ram tasks as background processes
                    cpu_send_task = asyncio.create_task(send_cpu(websocket=websocket))
                    ram_send_task = asyncio.create_task(send_ram(websocket=websocket))
                    ping_task = asyncio.create_task(ping(websocket=websocket))
                    bandwidth_task = asyncio.create_task(get_bandwidth(websocket=websocket))
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
                                ping_task.cancel()
                                bandwidth_task.cancel()
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