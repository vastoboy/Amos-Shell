# Amos-Shell Simple HTTP Reverse Shell


<img src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"> <img src="https://img.shields.io/badge/Elastic_Search-005571?style=for-the-badge&logo=elasticsearch&logoColor=white" alt="Elasticsearch"> <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux"><img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"><img src="https://img.shields.io/badge/VirtualBox-21416b?style=for-the-badge&logo=VirtualBox&logoColor=white" alt="Virtualbox"><img src="https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="sqlite">


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

### General Features
- **File Download (Client → Server)**: Exfiltrate files from the target using `getfile <path>`. Files are Base64 encoded for safe transit.
- **File Upload (Server → Client)**: Push files to the target machine using `sendfile <path>`. 
- **Screenshot Capture**: Capture the target's screen using the `screenshot` command.
- **Webcam Capture**: Capture a photo using the target's webcam via the `camshot` command.
- **System Profiling**: Harvests comprehensive platform information on first contact.
- **File Encryption**: Encrypt and decrypt files on the target machine using `encrypt <file> <password>` and `decrypt <file> <password>`.
- **AES-256-GCM**: Utilizes authenticated encryption to ensure confidentiality and integrity.
- **PBKDF2 Key Derivation**: Securely derives encryption keys from user-provided passwords.

## Prerequisites

- **Python 3.9+**
- **Elasticsearch**: Must be running locally (default: `http://localhost:9200`).
- **Required Python Packages**: 
  ```bash
  pip install -r requirements.txt
---

## Usage

### 1. Start the Server
```bash
cd Server
python main.py
```

### 2. Start the Client
```bash
cd Client
python main.py
```

### 3. Server Commands
Once the server is running, you can use the following commands:
- `guide` - Show the help menu
- `clients` - List all clients stored in the Elasticsearch index
- `connected` - Perform a live check to see which clients are currently online
- `shell <client_id>` - Open an interactive terminal session with a specific client
- `exit` - Shut down the server

### 4. Interactive Shell Commands
While inside a `shell <client_id>` session:
- Type standard OS commands (e.g., `cd`, `dir`, `ls`, `whoami`, `tasklist`)
- `screenshot` - Capture the target's screen
- `camshot` - Capture an image from the target's webcam
- `getfile <path>` - Download a file from the target
- `sendfile <path>` - Upload a file to the target
- `encrypt <file> <password>` - Encrypt a file on the target
- `decrypt <file> <password>` - Decrypt a file on the target
- `exit` - Return to the main server menu

---

## Disclaimer
**This project is for educational purposes only.** 
It is designed to demonstrate networking, threading, and system administration concepts in a controlled, ethical environment. Do not use this software on any system you do not own or have explicit permission to test. The authors are not responsible for any misuse or damage caused by this program.

