#!/bin/python3
import os
import sys
import time
import websocket
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from websockets.exceptions import ConnectionClosed
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis
from bokeh.palettes import Sunset6, TolRainbow4

load_dotenv()

token = os.getenv('TOKEN')
device = os.getenv('DEVICE_ID')
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename='tempestGraph.log', when='midnight', interval=1, backupCount = 10, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s - %(levelname)s = %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

NUM_POINTS = 1480 #24 hours
yAxis = []
xAxis = []
dirAxis = []
feelsLikeAxis = []
tempAxis = []
gustList = []

ws = websocket.WebSocket()
try:
    while True:
        try:  
            ws.connect(f"wss://ws.weatherflow.com/swd/data?token={token}")
        except Exception as e:
            exec_typ, exec_obj, exec_tb = sys.exc_info()
            logger.error(f"Exception on line {exec_tb.tb_lineno} :{e}")
            time.sleep(5)
        logger.info("Connected to Weatherflow Websocket")
        ws.send('{"type":listen_start", "device_id":' +  str(device) + ', "id": "Tempest"}')
        logger.info("Listen_start sent to websocket")
        while True:
            try:
                data = ws.recv()
                d = json.loads(data)
            except ConnectionClosed:
                logger.warning("Websocket connection close")
                time.sleep(1)
                break
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error("Excpetion on line " + str(exc_tb.tb_lineno) + ": " + str(e))
                ws.close()
                time.sleep(1)
                break
            try:
                if d['type'] == "obs_st":
                    windAvg = d['obs'][0][2] * 2.23694
                    windGust = d['obs'][0][3] * 2.23694
                    windDir = d['obs'][0][4]
                    feelsLike = (d['summary']['feels_like'] * (9/5)) + 32
                    temp = (d['obs'][0][7] * (9/5)) + 32

                    #Graph the data 
                    if len(yAxis) == NUM_POINTS:
                        yAxis.pop(0)
                        xAxis.pop(0)
                        dirAxis.pop(0)
                        feelsLikeAxis.pop(0)
                        tempAxis.pop(0)

                    yAxis.append(windGust)
                    logger.info("Wind Gust: " + str(windGust))
                    xAxis.append(datetime.now())
                    dirAxis.append(windDir)
                    logger.info("Wind Dir: " + str(windDir))
                    feelsLikeAxis.append(feelsLike)
                    logger.info("Feels Like: " + str(feelsLike))
                    tempAxis.append(temp)
                    logger.info("Temp: " + str(temp))

                    output_file(filename="/var/www/html/weather.html", title="Weather Graph")
                    p = figure(title="Local Weather", y_range=(0,max(yAxis)+2), x_axis_type="datetime", height=800, width=1400)
                    p.line(y = yAxis, x=xAxis)
                    p.xaxis.axis_label = "Time Stamp"
                    p.yaxis.axis_label = "Speed (mph)"
                    p.extra_y_ranges['dir'] = Range1d(0,360)
                    p.extra_y_ranges['feels'] = Range1d(min(min(feelsLikeAxis), min(tempAxis))-1, max(max(feelsLikeAxis), max(tempAxis))+1)
                    p.extra_y_ranges['temp'] = Range1d(min(min(feelsLikeAxis), min(tempAxis))-1, max(max(feelsLikeAxis), max(tempAxis))+1)

                    p.scatter(xAxis, dirAxis, y_range_name='dir', color='red')
                    ax2 = LinearAxis(y_range_name='dir', axis_label="Wind Dir")
                    red = Sunset6[5]
                    yellow = TolRainbow4[2]
                    green = TolRainbow4[1]
                    ax2.axis_label_text_color=red

                    p.line(y=feelsLikeAxis, x=xAxis, line_color = yellow, y_range_name = 'feels')
                    ax3 = LinearAxis(y_range_name="feels", axis_label="Feels Like")
                    ax3.axis_label_text_color = yellow

                    p.line(y=tempAxis, x=xAxis, line_color = green, y_range_name = 'temp')
                    ax4 = LinearAxis(y_range_name="temp", axis_label="Temp")
                    ax4.axis_label_text_color = green

                    p.add_layout(ax2, 'left')
                    p.add_layout(ax3, 'left')
                    p.add_layout(ax4, 'left')
                    save(p)
                    logger.debug("Chart written")
            except Exception as e:
                xc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error("Excpetion on line " + str(exc_tb.tb_lineno) + ": " + str(e))
                ws.close()
                time.sleep(1)
                break
except KeyboardInterrupt:
    logger.info("Keyboard Interrupt. Exiting")
    ws.send('{"type":"listen_stop", "device_id":' + str(device) + ', "id":"Tempest"}')
    ws.close()
    exit()
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    logger.critical("Excpetion on line " + str(exc_tb.tb_lineno) + ": " + str(e))
