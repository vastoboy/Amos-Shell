import json
import socket
import getpass
import datetime
import platform
from getmac import get_mac_address as gma
from client_settings import SERVER_IP


class DataHarvester:

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))  # Connect to Google's public DNS server
                return s.getsockname()[0]  # Return the local IP address used for this connection
        except Exception as e:
            return None


    # returns client system information to the server
    def get_platform_info(self):

        system_info = {
                         "mac-address": gma(),
                         "ip": self.get_local_ip(),
                         "os": platform.uname().system,
                         "system-name": platform.uname().node,
                         "release": platform.uname().release,
                         "version": platform.uname().version,
                         "machine": platform.uname().machine,
                         "date-joined": str(datetime.date.today()),
                         "time-joined": str(datetime.datetime.now().time()),
                         "user": getpass.getuser()
                    }

        system_info = json.dumps(system_info)

        return system_info


