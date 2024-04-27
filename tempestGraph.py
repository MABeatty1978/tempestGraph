#!/bin/python3
import os
import sys
import time
import websocket
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from websockets.exceptions import ConnectionClosed
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis
from bokeh.layouts import column
load_dotenv()

token = os.getenv('TOKEN')
device = os.getenv('DEVICE_ID')
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename='log/tempestGraph.log', when='midnight', interval=1, backupCount = 10, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s - %(levelname)s = %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
parser = argparse.ArgumentParser()
parser.add_argument('--debug', help='Turn on debug logging', action='store_true')
args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)
    logger.debug('Started in debug')
else:
    logger.setLevel(logging.INFO)

NUM_POINTS = 1480 #24 hours
windgustAxis = []
windavgAxis = []
xAxis = []
dirAxis = []
feelsLikeAxis = []
tempAxis = []
gustList = []
pressureAxis=[]
humidityAxis=[]
uvAxis=[]
luxAxis=[]
radiationAxis=[]
rainperiodAxis=[]
raindayAxis=[]
rainperiodncAxis=[]
raindayncAxis=[]
lightCountAxis=[]
lightDistAxis=[]
h=800
w=1500

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
                logger.error("Exception on line " + str(exc_tb.tb_lineno) + ": " + str(e))
                ws.close()
                time.sleep(1)
                break
            logger.info("Message received type: " + d['type'])
            logger.debug(d)
            try:
                if d['type'] == "obs_st":
                    windAvg = d['obs'][0][2] * 2.23694
                    windGust = d['obs'][0][3] * 2.23694
                    windDir = d['obs'][0][4]
                    feelsLike = (d['summary']['feels_like'] * (9/5)) + 32
                    temp = (d['obs'][0][7] * (9/5)) + 32
                    pressure = d['obs'][0][6]
                    humidity = d['obs'][0][8]
                    lux=d['obs'][0][9]
                    uv=d['obs'][0][10]
                    radiation=d['obs'][0][11]
                    rainperiod=d['obs'][0][12]
                    lightningdist=d['obs'][0][14]
                    lightningcount=d['obs'][0][15]
                    battery=d['obs'][0][16]
                    rainday=d['obs'][0][18]
                    rainperiodnc=d['obs'][0][19]
                    raindaync=d['obs'][0][20]

                    #Load the arrays 
                    if len(xAxis) == NUM_POINTS:
                        xAxis.pop(0)
                        windgustAxis.pop(0)
                        dirAxis.pop(0)
                        feelsLikeAxis.pop(0)
                        tempAxis.pop(0)
                        windavgAxis.pop(0)
                        pressureAxis.pop(0)
                        humidityAxis.pop(0)
                        uvAxis.pop(0)
                        luxAxis.pop(0)
                        radiationAxis.pop(0)
                        rainperiodAxis.pop(0)
                        raindayAxis.pop(0)
                        rainperiodncAxis.pop(0)
                        raindaymcAxis.pop(0)
                        lightCountAxis.pop(0)
                        lightDistAxis.pop(0)

                    windgustAxis.append(windGust)
                    windavgAxis.append(windAvg)
                    xAxis.append(datetime.now())
                    dirAxis.append(windDir)
                    feelsLikeAxis.append(feelsLike)
                    tempAxis.append(temp)
                    pressureAxis.append(pressure)
                    humidityAxis.append(humidity)
                    uvAxis.append(uv)
                    luxAxis.append(lux)
                    radiationAxis.append(radiation)
                    rainperiodAxis.append(rainperiod)
                    raindayAxis.append(rainday)
                    rainperiodncAxis.append(rainperiodnc)
                    raindayncAxis.append(raindaync)
                    lightCountAxis.append(lightningcount)
                    lightDistAxis.append(lightningdist)

                    logger.debug('Wind gust ' + str(windgustAxis))
                    logger.debug('Wind avg ' + str(windavgAxis))
                    logger.debug('Wind dir ' + str(dirAxis))
                    logger.debug('Temp ' + str(tempAxis))
                    logger.debug('Feels like ' + str(feelsLikeAxis))
                    logger.debug('Pressure ' + str(pressureAxis))
                    logger.debug('Humidity ' + str(humidityAxis))
                    logger.debug('Radiation ' + str(radiationAxis))
                    logger.debug('UV ' + str(uvAxis))
                    logger.debug('Lux ' + str(luxAxis))
                    logger.debug('Rain Period ' + str(rainperiodAxis))
                    logger.debug('Rain Day ' + str(raindayAxis))
                    logger.debug('Rain Period NC ' + str(rainperiodncAxis))
                    logger.debug('Rain Day ' + str(raindayncAxis))
                    logger.debug('Lightning Count ' + str(lightningcount))
                    logger.debug('Lightning Dist ' + str(lightningdist))

                    #Graph the data
                    #Temperature graph
                    output_file(filename="/var/www/html/weather.html", title="Weather Graph")
                    tempGraph = figure(title="Temperature", x_axis_type="datetime", height=h, width=w)
                    tempGraph.line(xAxis, feelsLikeAxis, line_color = 'yellow', legend_label='Feels Like')
                    tempGraph.line(xAxis, tempAxis, line_color = 'green', legend_label='Temp')

                    #Wind graph
                    windGraph = figure(title='Wind', x_axis_type='datetime', height=h, width=w)
                    windGraph.y_range = Range1d(0,360)
                    windGraph.extra_y_ranges['speed'] = Range1d(0, max(windgustAxis)+1)
                    windGraph.scatter(xAxis, dirAxis, color='red')
                    wsAxis = LinearAxis(y_range_name='speed', axis_label='Wind Speed')
                    windGraph.line(xAxis, windgustAxis, y_range_name='speed', legend_label='Max Gust', line_color='blue')
                    windGraph.line(xAxis, windavgAxis, y_range_name='speed', legend_label='Average', line_color='red')
                    windGraph.add_layout(wsAxis, 'left')

                    #Environment Conditions
                    envGraph = figure(title='Environment', x_axis_type='datetime', height=h, width=w)
                    envGraph.y_range =Range1d(0, max(uvAxis))
                    envGraph.yaxis.axis_label="UV"
                    envGraph.yaxis.axis_label_text_color='red'
                    envGraph.extra_y_ranges['pres'] = Range1d(min(pressureAxis)-1, max(pressureAxis)+1)
                    envGraph.extra_y_ranges['humid'] = Range1d(0,100)
                    envGraph.extra_y_ranges['ill'] = Range1d(0, max(luxAxis)+100)
                    envGraph.extra_y_ranges['rad'] = Range1d(0, max(radiationAxis))
                    envPaxis=LinearAxis(y_range_name='pres', axis_label='Pressure Mb')
                    envHaxis=LinearAxis(y_range_name='humid', axis_label='Humidity')
                    envLaxis=LinearAxis(y_range_name='ill', axis_label='Illuminance')
                    envRaxis=LinearAxis(y_range_name='rad', axis_label='Solar Radiation')
                    envGraph.line(x=xAxis, y=uvAxis, color='red')
                    envGraph.line(x=xAxis, y=pressureAxis, y_range_name='pres', color='blue')
                    envGraph.line(x=xAxis, y=humidityAxis, y_range_name='humid', color='green')
                    logger.debug("Lux " + str(luxAxis))
                    envGraph.line(x=xAxis, y=luxAxis, y_range_name='ill', color='aqua')
                    envGraph.line(x=xAxis, y=radiationAxis, y_range_name='rad', color='orange')
                    envPaxis.axis_label_text_color='blue'
                    envHaxis.axis_label_text_color='green'
                    envLaxis.axis_label_text_color='aqua'
                    envRaxis.axis_label_text_color='orange'
                    envGraph.add_layout(envPaxis,'left')
                    envGraph.add_layout(envRaxis,'left')
                    envGraph.add_layout(envHaxis,'right')
                    envGraph.add_layout(envLaxis,'right')
                    
                    save(column(tempGraph, windGraph, envGraph))
                    logger.info("Weather file written")
                    
                    output_file(filename="/var/www/html/rain.html", title="Rainfall")
                    #Rain Conditions
                    rainGraph=figure(title='Rain', x_axis_type='datetime', height=h, width=w)
                    rainGraph.y_range=Range1d(0, max(max(raindayAxis), max(raindayncAxis))+1)
                    rainGraph.extra_y_ranges['period'] = Range1d(0, max(max(rainperiodAxis), max(rainperiodncAxis))+1)
                    rainPeraxis=LinearAxis(y_range_name='period', axis_label='Period')
                    rainGraph.line(x=xAxis, y=rainday, color='aqua')
                    rainGraph.line(x=xAxis, y=raindaync, color='blue')
                    rainGraph.vbar(x=xAxis, top=rainperiod,  color='palegreen')
                    rainGraph.vbar(x=xAxis, top=rainperiodnc,  color='green')
                    rainGraph.add_layout(rainPeraxis,'left')

                    #Lightning
                    lightGraph=figure(title='Lightning Strikes', x_axis_type='datetime', height=h, width=w)
                    lightGraph.y_range=Range1d(0, max(lightCountAxis)+1)
                    lightGraph.extra_y_ranges['dist'] = Range1d(0, max(lightDistAxis)+1)
                    lightax=LinearAxis(y_range_name='dist', axis_label='Distance')
                    lightGraph.scatter(x=xAxis, y=lightCountAxis, color='red')
                    lightGraph.vbar(x=xAxis, top=lightDistAxis, color='blue')
                    lightGraph.add_layout(lightax, 'left')
                    save(column(lightGraph, rainGraph))
                    
                    logger.info("Rain file written")
            except Exception as e:
                xc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error("Exception on line " + str(exc_tb.tb_lineno) + ": " + str(e))
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
    logger.critical("Exception on line " + str(exc_tb.tb_lineno) + ": " + str(e))
    exit()
