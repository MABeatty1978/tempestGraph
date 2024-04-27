#!/usr/bin/python3

import select
import json
import logging
import os
import socket
import struct
import time
import argparse
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis
from datetime import datetime
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Turn on debug logging", action="store_true")
args = parser.parse_args()
load_dotenv()
token = os.getenv('TOKEN')
station =  os.getenv('STATION_ID')
server = os.getenv('SERVER_DIR')
logfile = os.getenv('LOGFILE')
NUM_POINTS=28800 #1 day
#Axis arrays
xAxis=[]
windS=[]
windD=[]
logfile='log/udpwind.log'
#Setup Logging
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename=logfile, when='midnight', interval=1, backupCount=10, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
if args.debug:
    logger.setLevel(logging.DEBUG)
    logger.debug("forecast.py started in debug")
else:
    logger.setLevel(logging.INFO)

#Listen to UDP
def create_broadcast_listener_socket(broadcast_ip, broadcast_port):

    b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    b_sock.bind(('', broadcast_port))

    mreq = struct.pack("4sl", socket.inet_aton(broadcast_ip), socket.INADDR_ANY)
    b_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return b_sock



# ip/port to listen to
BROADCAST_IP = '239.255.255.255'
BROADCAST_PORT = 50222

# create the listener socket
sock_list = [create_broadcast_listener_socket(BROADCAST_IP, BROADCAST_PORT)]
logger.info('Listening for UDP messages')
while True:
    # small sleep otherwise this will loop too fast between messages and eat a lot of CPU
    time.sleep(0.01)

    # wait until there is a message to read
    readable, writable, exceptional = select.select(sock_list, [], sock_list, 0)
    # for each socket with a message
    for s in readable:
        data, addr = s.recvfrom(4096)
        # convert data to json
        d = json.loads(data)
        logger.debug(d) 
        if d['type'] == 'hub_status':
            logger.info('Hub Status - Uptime: ' + str(d['uptime']) + ' RSSI: ' + str(d['rssi'])) 
        elif d['type'] == 'rapid_wind':
            if len(xAxis)==NUM_POINTS:
                xAxis.pop(0)
                windS.pop(0)
                windD.pop(0)
            xAxis.append(datetime.now())
            windS.append(round(d['ob'][1] * 2.23694, 1))
            windD.append(d['ob'][2])
            logger.debug(str(windS))
            logger.debug(str(windD))

            output_file(filename='/var/www/html/rapidwind.html', title='Rapid Wind')
            windGraph = figure(title='Rapid Wind', x_axis_type='datetime', height=800, width=1500)
            windGraph.y_range=Range1d(0, max(windS)+1)
            windGraph.extra_y_ranges['dir'] = Range1d(0,360)
            windGraph.line(xAxis, windS)
            wdAxis = LinearAxis(y_range_name='dir', axis_label='Wind Direction')
            windGraph.scatter(xAxis, windD, y_range_name='dir', color='red')
            windGraph.add_layout(wdAxis, 'left')
            save(windGraph)
            logger.debug("Graph written")
            
