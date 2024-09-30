import socket
import getpass
import requests
import datetime
import platform
from datetime import timedelta
from getmac import get_mac_address as gma


class DataHarvester:

    # returns client system information to the server
    def get_platform_info(self):

        system_info = {
                         "mac-address": gma(),
                         "ip": "",
                         "os": platform.uname().system,
                         "system-name": platform.uname().node,
                         "release": platform.uname().release,
                         "version": platform.uname().version,
                         "machine": platform.uname().machine,
                         "date-joined": str(datetime.date.today()),
                         "time-joined": str(datetime.datetime.now().time()),
                         "user": getpass.getuser()
                    }

        return system_info


