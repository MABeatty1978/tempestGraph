#!/usr/bin/python3

import requests
import logging
import os
import argparse
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from bokeh.plotting import figure, output_file, save
from bokeh.models import Range1d, LinearAxis
from bokeh.palettes import Category10
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
xAxis=[]
temp=[]
wind=[]
precipchance=[]
baro=[]

logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename=logfile, when='midnight', interval=1, backupCount=10, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

logger.info("Connecting to weatherflow")
URL = "https://swd.weatherflow.com/swd/rest/better_forecast?station_id={}&units_pressure=inhg&units_temp=f&units_wind=mph&units_precip=in&units_distance=mi&token={}".format(station, token)
logger.debug("URL: " + URL)
r = requests.get(url = URL)
logger.info("Conection returned with status code: " + str(r.status_code))
d = r.json()
month = datetime.now().month
year = datetime.now().year
startday = d['forecast']['hourly'][0]['local_day']
monthrolled=False
blue=Category10[4][0]
orange=Category10[4][1]
green=Category10[4][2]
red=Category10[4][3]
fname = server + "forecast.html"

for f in d['forecast']['hourly']:
    if f['local_day'] < startday:
        if not monthrolled:
            monthrolled=True
            if month == 12:
                year = year + 1 
            month = month +1
            

    xAxis.append(datetime(year, month, f['local_day'], f['local_hour']))
    temp.append(f['air_temperature'])
    precipchance.append(f['precip_probability'])
    wind.append(f['wind_gust'])
    baro.append(f['sea_level_pressure'])

logger.debug(xAxis)
logger.debug(temp)
logger.debug(wind)
logger.debug(precipchance)
logger.debug(baro)

output_file(filename=fname, title="10 Day Hourly Forecast")
p = figure(title="Forecast " + str(datetime.now()), width=1500, x_axis_type='datetime')
p.extra_y_ranges['wind'] = Range1d(min(wind), max(wind))
p.extra_y_ranges['precipchance'] = Range1d(0,100)
p.extra_y_ranges['baro'] = Range1d (min(baro)-.1, max(baro)+.1)

p.line(y=temp, x=xAxis)
p.line(y=wind, x=xAxis, line_color=green, y_range_name = 'wind')
p.yaxis.axis_label = 'Temp'
p.yaxis.axis_label_text_color = blue
p.xaxis.ticker.desired_num_ticks =72 
p.xaxis.major_label_orientation = 'vertical' 
ax2 = LinearAxis(y_range_name='wind', axis_label="Wind Speed")
ax2.axis_label_text_color=green
p.line(y=precipchance, x=xAxis, line_color=orange, y_range_name='precipchance')
ax3 = LinearAxis(y_range_name='precipchance', axis_label="Precip Chance")
ax3.axis_label_text_color=orange
p.line(y=baro, x=xAxis, line_color=red, y_range_name='baro')
ax4 = LinearAxis(y_range_name='baro', axis_label="Pressure")
ax4.axis_label_text_color=red
p.add_layout(ax2, 'left')
p.add_layout(ax3, 'left')
p.add_layout(ax4, 'left')

save(p)
logger.info("Chart Written")
