from EsHandler import EsHandler

# Server's IP address or hostname
SERVER_IP = 'localhost'

# Server Port
SERVER_PORT = 8080

# Instance of (ES_HANDLER) will be used to interact with the Elasticsearch service.
ES_HANDLER = EsHandler("amos-index", "http://localhost:9200")

# Path to use for signifying a command request from a client using HTTP GET
CMD_REQUEST = "/amos?center="

# Path to use for signifying the current working directory from a client using HTTP POST
CWD_RESPONSE = "/title"

# Path to use for signifying command output or errors from a client using HTTP POST
RESPONSE = "/inventory"

# Path to use for signifying command output or errors from a client using HTTP POST
CMD_RESPONSE = "/inventory"

# Path to use for signifying sending client credentials
CLIENT_CREDENTIALS = "/credentials"

# POST variable name to use for assigning to command output from a client
RESPONSE_KEY = "index"

# Command input timeout setting in seconds; 225 is about right for Azure; set to NONE if not needed
INPUT_TIMEOUT = 20

# Run this command automatically to prevent Azure and other hosting environments from killing our active session
KEEP_ALIVE_CMD = "time /T"  # Windows only

CONNECTED_CLIENTS = {}
