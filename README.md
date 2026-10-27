# Amos-Shell Simple HTTP Reverse Shell

A lightweight C2 (Command & Control) framework that uses HTTP for communication between a server and multiple remote clients. 

## Features

### Core Architecture
- **Multi-Client Support**: Utilizes `ThreadingHTTPServer` to handle concurrent connections from multiple clients.
- **Elasticsearch Backend**: Automatically harvests and stores client metadata (MAC address, IP, OS, system name, etc.) for persistent tracking.
- **Asynchronous Command Queue**: Thread-safe command and response queues ensure reliable communication between the operator and clients.
- **Dynamic Prompt**: The interactive shell automatically tracks and displays the client's current working directory (CWD) in the prompt.

### Client Management
- **Interactive Shell**: Drop into a specific client's terminal using `shell <client_id>`.
- **Live Liveness Checks**: The `connected` command actively pings all registered clients in parallel to verify if they are still online, instantly pruning dead connections.
- **Client Registry**: View all historically indexed clients via the `clients` command.

### Command & Control
- **Remote Command Execution**: Execute standard shell commands on the client machine and receive standard output/error.
- **Directory Traversal**: Seamless `cd` handling on the client side that updates the server's prompt context.

### File Transfer & Exfiltration
- **File Download (Client → Server)**: Exfiltrate files from the target using `getfile <path>`. Files are Base64 encoded for safe transit.
- **File Upload (Server → Client)**: Push files to the target machine using `sendfile <path>`. 

### Surveillance & Data Collection
- **Screenshot Capture**: Capture the target's screen using the `screenshot` command.
- **Webcam Capture**: Capture a photo using the target's webcam via the `camshot` command.
- **System Profiling**: Harvests comprehensive platform information on first contact.

### Data Protection
- **File Encryption**: Encrypt and decrypt files on the target machine using `encrypt <file> <password>` and `decrypt <file> <password>`.
- **AES-256-GCM**: Utilizes authenticated encryption to ensure confidentiality and integrity.
- **PBKDF2 Key Derivation**: Securely derives encryption keys from user-provided passwords.

---

## Prerequisites

- **Python 3.9+**
- **Elasticsearch**: Must be running locally (default: `http://localhost:9200`).
- **Required Python Packages**: 
  ```bash
  pip install -r requirements.txt