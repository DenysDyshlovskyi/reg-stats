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
import aiofiles
import shutil
import subprocess

def main():
    # Define variables
    DEBUG = True
    DEBUG_FILE_PATH = os.path.join(os.getcwd(), "debug.txt")
    CPU_SEND_INTERVAL = 5
    RAM_SEND_INTERVAL = 5
    PING_INTERVAL = 2
    BANDWIDTH_INTERVAL = 1
    BANDWIDTH_SEND_DELAY = 5
    READ_WRITE_INTERVAL = 1800
    READ_WRITE_DATA_MB = 512 #MB
    GET_STORAGE_INTERVAL = 1800
    GET_UPTIME_INTERVAL = 3600
    GET_PROCESSES_INTERVAL = 120

    # write pid to text file
    with open(os.path.join(os.getcwd(), "pid.txt"), 'w') as file:
        file.write(str(os.getpid()))
        file.close()

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
            WEBSOCKET_PREFIX = vars["ws_prefix"]
            HTTP_PREFIX = vars["http_prefix"]

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

                    download_speed = (received_bandwidth / 1024) # KB/s
                    upload_speed = (transmitted_bandwidth / 1024) # KB/s

                    return received_bandwidth, transmitted_bandwidth, download_speed, upload_speed

                # Sends bandwidth and download and upload speed to websocket
                async def get_bandwidth(websocket):
                    while True:
                        try:
                            # Get bandwidth from other function
                            received_bandwidth, transmitted_bandwidth, download_speed, upload_speed = await measure_bandwidth()

                            # Send bandwidth through websocket
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'bandwidth',
                                'received': received_bandwidth,
                                'transmitted': transmitted_bandwidth,
                                'bandwidth_interval': BANDWIDTH_INTERVAL,
                                'client_id': client_id
                            }))

                            # Send upload and download speed through websocket
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'download_upload',
                                'upload_speed': upload_speed,
                                'download_speed': download_speed,
                                'bandwidth_interval': BANDWIDTH_INTERVAL,
                                'client_id': client_id
                            }))

                            await asyncio.sleep(BANDWIDTH_SEND_DELAY)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(BANDWIDTH_SEND_DELAY)

                # Gets read and write speed for disks on computer            
                async def get_read_write(websocket):
                    while True:
                        try:
                            data = {}
                            # Get list of drives on computer
                            possible_drives = [f"{chr(65 + i)}" for i in range(26)]  # A: to Z:
                            drives = [drive for drive in possible_drives if os.path.exists(f"{drive}:\\")]

                            # Loop through drives
                            for letter in drives:
                                # Create path to write and read to
                                test_dir = os.path.join(f"{letter}:\\", "regstats_rw_test")
                                os.makedirs(test_dir, exist_ok=True)

                                # Define test file path
                                test_file = os.path.join(test_dir, "regstats_rw_test.txt")

                                try:
                                    # Take timestamp of start
                                    start_time = time.time()
                                    async with aiofiles.open(test_file, 'w', encoding='utf-8') as f:
                                        # Try to write
                                        small_string = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 26 characters
                                        total_size = READ_WRITE_DATA_MB * 1024 * 1024
                                        chunk_size = 1024 * 1024 #1mb

                                        while total_size > 0:
                                            string_chunk = (small_string * (chunk_size // len(small_string)))[:chunk_size]
                                            await f.write(string_chunk)
                                            total_size -= len(string_chunk)
                                except Exception:
                                    write_to_debug(f"Error when writing to {letter}: {traceback.format_exc()}")

                                # Measure how long it took
                                end_time = time.time()
                                time_taken = end_time - start_time
                                mbps = round((READ_WRITE_DATA_MB / time_taken), 1)

                                if letter not in data:
                                    data[letter] = {}

                                # Write to data
                                data[letter]["write"] = {
                                    "total_mb": READ_WRITE_DATA_MB,
                                    "start_time": start_time,
                                    "end_time": end_time,
                                    "time_taken": time_taken,
                                    "mbps": mbps
                                }

                                # Do everything again for read
                                try:
                                    # Take timestamp of start
                                    start_time = time.time()
                                    async with aiofiles.open(test_file, 'r', encoding='utf-8') as f:
                                        await f.read()
                                except Exception:
                                    write_to_debug(f"Error when reading to {letter}: {traceback.format_exc()}")

                                # Measure how long it took
                                end_time = time.time()
                                time_taken = end_time - start_time
                                mbps = round((READ_WRITE_DATA_MB / time_taken), 1)

                                # Write to data
                                data[letter]["read"] = {
                                    "total_mb": READ_WRITE_DATA_MB,
                                    "start_time": start_time,
                                    "end_time": end_time,
                                    "time_taken": time_taken,
                                    "mbps": mbps
                                }

                                # Cleanup
                                if os.path.exists(test_dir):
                                    shutil.rmtree(test_dir)

                            # Send data in websocket
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'read_write',
                                'data': data,
                                'client_id': client_id
                            }))
                            await asyncio.sleep(READ_WRITE_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(READ_WRITE_INTERVAL)

                async def get_storage(websocket):
                    while True:
                        try:
                            data = {}
                            # Get list of drives on computer
                            possible_drives = [f"{chr(65 + i)}" for i in range(26)]  # A: to Z:
                            drives = [drive for drive in possible_drives if os.path.exists(f"{drive}:\\")]

                            for letter in drives:
                                if letter not in data:
                                    data[letter] = {}

                                # Get total used and avaiable storage
                                total, used, free = shutil.disk_usage(f"{letter}:\\")

                                # Convert bytes to GB for easier readability
                                total_gb = round((total / (1024 ** 3)), 1)
                                used_gb = round((used / (1024 ** 3)), 1)
                                free_gb = round((free / (1024 ** 3)), 1)

                                # Write to data
                                data[letter] = {
                                    "total_gb": total_gb,
                                    "used_gb": used_gb,
                                    "free_gb": free_gb
                                }

                            # Send through websocket
                            await websocket.send(json.dumps({
                                'sender': 'c',
                                'type': 'storage',
                                'data': data,
                                'client_id': client_id
                            }))
                            await asyncio.sleep(GET_STORAGE_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(GET_STORAGE_INTERVAL)

                async def get_uptime(websocket):
                    while True:
                        try:
                            # Define command to get total seconds of uptime
                            command = '''powershell "((Get-Date) - (Get-CimInstance -ClassName Win32_OperatingSystem | Select LastBootUpTime).LastBootUpTime).TotalSeconds"'''

                            # Run the command
                            process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                            
                            # Capture the output (uptime in seconds)
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0:
                                uptime = stdout.decode().strip()  # Output in seconds

                                # Send to websocket
                                await websocket.send(json.dumps({
                                    'sender': 'c',
                                    'type': 'uptime',
                                    'seconds': round(float(uptime), 1),
                                    'client_id': client_id
                                }))
                            else:
                                write_to_debug(f"Error: {stderr.decode().strip()}")

                            await asyncio.sleep(GET_UPTIME_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(GET_UPTIME_INTERVAL)

                async def get_processes(websocket):
                    while True:
                        try:
                            # Get all processes with their names, cpu usage and ram usage
                            command = '''powershell "$cpu_cores = (Get-CimInstance -ClassName Win32_ComputerSystem).NumberOfLogicalProcessors; Get-Process | Select-Object Name, CPU, @{Name='MemoryUsageMB';Expression={[math]::round($_.WorkingSet / 1MB, 2)}} | ForEach-Object {$_.CPU = if ($_.CPU) { [math]::round($_.CPU / $cpu_cores, 2) } else { 0 } $_} | ConvertTo-Json"'''

                            # Run the command
                            process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                            
                            # Capture the output
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0:
                                final_dict = {}
                                json_output = stdout.decode().strip()

                                # Convert the json to a dictionary
                                processes_dict = json.loads(json_output)

                                # Loop through it
                                for item in processes_dict:
                                    process_name = item["Name"]
                                    if process_name not in final_dict:
                                        final_dict[process_name] = {
                                            "cpu": 0,
                                            "ram": 0
                                        }

                                    # Add to final dict
                                    if item["CPU"]:
                                        final_dict[process_name]["cpu"] += item["CPU"]

                                    if item["MemoryUsageMB"]:
                                        final_dict[process_name]["ram"] += item["MemoryUsageMB"]

                                # Send to websocket
                                await websocket.send(json.dumps({
                                    'sender': 'c',
                                    'type': 'processes',
                                    'processes': final_dict,
                                    'client_id': client_id
                                }))
                            else:
                                write_to_debug(f"Error: {stderr.decode().strip()}")

                            await asyncio.sleep(GET_PROCESSES_INTERVAL)
                        except Exception:
                            write_to_debug(traceback.format_exc())
                            await asyncio.sleep(GET_PROCESSES_INTERVAL)

                async with websockets.connect(uri, additional_headers=headers) as websocket:
                    # Start background processes
                    task_list = []
                    task_list.append(asyncio.create_task(send_cpu(websocket=websocket)))
                    task_list.append(asyncio.create_task(send_ram(websocket=websocket)))
                    task_list.append(asyncio.create_task(ping(websocket=websocket)))
                    task_list.append(asyncio.create_task(get_bandwidth(websocket=websocket)))
                    task_list.append(asyncio.create_task(get_read_write(websocket=websocket)))
                    task_list.append(asyncio.create_task(get_storage(websocket=websocket)))
                    task_list.append(asyncio.create_task(get_uptime(websocket=websocket)))
                    task_list.append(asyncio.create_task(get_processes(websocket=websocket)))
                    while True:
                        # Wait for messages from websocket
                        try:
                            response = await websocket.recv()
                            write_to_debug(f"Response received: {response}")
                        except Exception:
                            write_to_debug(f"Failed receiving responses: {traceback.format_exc()}")
                            for task in task_list:
                                if task:
                                    task.cancel()
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