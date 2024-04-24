#!/usr/bin/python3

import requests
import logging
import os
import argparse
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import column
from bokeh.models import Range1d, LinearAxis
#from bokeh.palettes import Category20c, Category20b
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

#Axis arrays
xAxis=[]
temp=[]
feelslike=[]
uv=[]
humidity=[]
windgust=[]
windavg=[]
winddir=[]
precipchance=[]
baro=[]
condColor=[]
conditions=[]
precip=[]

#Setup Logging
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename=logfile, when='midnight', interval=1, backupCount=10, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

#Connect to API
logger.info("Connecting to weatherflow")
URL = "https://swd.weatherflow.com/swd/rest/better_forecast?station_id={}&units_pressure=inhg&units_temp=f&units_wind=mph&units_precip=in&units_distance=mi&token={}".format(station, token)
logger.debug("URL: " + URL)
r = requests.get(url = URL)
logger.info("Conection returned with status code: " + str(r.status_code))
d = r.json()

#Variables and logic to handle rolling the month
month = datetime.now().month
year = datetime.now().year
startday = d['forecast']['hourly'][0]['local_day']
monthrolled=False


#Conditions color definitions
rain='mediumseagreen'
lightRain = 'palegreen'
heavyRain = 'darkgreen'
stormslikely='darkred'
stormspossible='red'
foggy='silver'
snowpossible='skyblue'
snowlikely='blue'
winterymixpossible='magenta'
winterymixlikely='darkorchid'

fname = server + "forecast.html"

for f in d['forecast']['hourly']:
    if f['local_day'] < startday:
        if not monthrolled:
            monthrolled=True
            if month == 12:
                year = year + 1 
            month = month +1        
    logger.debug(str(datetime(year, month, f['local_day'], f['local_hour'])) + " Temp: " + " " + str(f['air_temperature']) + " Precip Prob: " + str(f['precip_probability']) + " Wind gust: " + str(f['wind_gust']) + " Baro: " + str(f['sea_level_pressure']) + " Conditions: " + f['conditions']) 
    xAxis.append(datetime(year, month, f['local_day'], f['local_hour']))
    temp.append(f['air_temperature'])
    precipchance.append(f['precip_probability'])
    windgust.append(f['wind_gust'])
    windavg.append(f['wind_avg'])
    winddir.append(f['wind_direction'])
    baro.append(f['sea_level_pressure'])
    conditions.append(f['conditions'])
    precip.append(f['precip'])
    humidity.append(f['relative_humidity'])
    feelslike.append(f['feels_like'])
    uv.append(f['uv'])

    #Set sky conditions bar colors
    if f['conditions'] == "Thunderstorms Possible":
        condColor.append(stormspossible)
    elif f['conditions'] == "Thunderstorms Likely":
        condColor.append(stormslikely)
    elif f['conditions'] == "Very Light Rain" or f['conditions'] == "Light Rain" or f['conditions'] == "Partly Cloudy" or f['conditions'] == "Cloudy":
        condColor.append(lightRain)
    elif f['conditions'] == "Rain Likely" or f['conditions'] == "Rain Possible" or f['conditions'] == "Moderate Rain":
        condColor.append(rain)
    elif f['conditions'] == "Heavy Rain" or f['conditions'] == "Extreme Rain":
        condColor.append(heavyRain)
    elif f['conditions'] == 'Snow Possible':
        condColor.append(snowPossible)
    elif f['conditions'] == 'Snow Likely':
        condColor.append(snowLikely)
    elif f['conditions'] == 'Wintery Mix Possible':
        condColor.append(winterymixpossible)
    elif f['conditions'] == 'Wintery Mix Likely':
        condColor.append(winterymixlikely)
    else:
        condColor.append('red')


output_file(filename=fname, title="10 Day Hourly Forecast")
p = figure(title="Forecast " + str(datetime.now()), width=1500, x_axis_type='datetime')
p.extra_y_ranges['baro'] = Range1d (min(baro)-.1, max(baro)+.1)
p.extra_y_ranges['feels'] = Range1d (min(temp), max(temp))
p.extra_y_ranges['humidity'] = Range1d (0,100)
p.extra_y_ranges['uv'] = Range1d(0,max(uv))
p.line(y=temp, x=xAxis)
p.yaxis.axis_label = 'Temp'
p.yaxis.axis_label_text_color = 'blue'
p.xaxis.ticker.desired_num_ticks =72 
p.xaxis.major_label_orientation = 'vertical' 
p.line(y=baro, x=xAxis, y_range_name='baro', line_color='purple')
ax2 = LinearAxis(y_range_name='baro', axis_label="Pressure")
ax2.axis_label_text_color='purple'
p.add_layout(ax2, 'left')
p.line(x=xAxis, y=feelslike, y_range_name='feels', line_color='green')
ax3 = LinearAxis(y_range_name='feels', axis_label="Feels Like")
ax3.axis_label_text_color='green'
p.add_layout(ax3, 'left')
p.line(x=xAxis, y=uv, y_range_name='uv', line_color='red')
ax4 = LinearAxis(y_range_name='uv', axis_label="UV")
ax4.axis_label_text_color='red'
p.add_layout(ax4, 'right')
p.line(x=xAxis, y=humidity, y_range_name='humidity', line_color='black')
ax5 = LinearAxis(y_range_name='humidity', axis_label='Humidity')
ax5.axis_label_text_color='black'
p.add_layout(ax5, 'right')

conditions = figure(title="Precipitation", width=1500, x_axis_type='datetime')
conditions.extra_y_ranges['precip'] = Range1d(0, max(precip))
conditions.y_range = Range1d(0, 100)
conditions.yaxis.axis_label="Chance of Precipitation/Type"
conditions.vbar(x=xAxis, top=precipchance, width=.5, line_width=5, color=condColor)
conditions.line(x=xAxis, y=precip, y_range_name='precip', color='blue')
conditionsax2 = LinearAxis(y_range_name='precip', axis_label="Rain Rate Per Hour")
conditionsax2.axis_label_text_color='blue'
conditions.add_layout(conditionsax2, 'left')
conditions.xaxis.ticker.desired_num_ticks=72
conditions.xaxis.major_label_orientation = 'vertical'

windgraph = figure(title="Wind", width=1500, x_axis_type='datetime')
windgraph.yaxis.axis_label="Wind Gust"
windgraph.yaxis.axis_label_text_color = 'blue'
windgraph.y_range = Range1d(0, max(windgust)+1)
windgraph.xaxis.ticker.desired_num_ticks=72
windgraph.xaxis.major_label_orientation = 'vertical'
windgraph.extra_y_ranges['winddir'] = Range1d(0,360)
windgraph.extra_y_ranges['windavg'] = Range1d(0, max(windgust)+1)

windgraph.line(x=xAxis, y=windgust)
windgraph.scatter(xAxis, winddir, y_range_name='winddir', color='red')
windgraph.line(xAxis, windavg, y_range_name='windavg', color='green')
winddiraxis = LinearAxis(y_range_name='winddir', axis_label='Wind Dir')
winddiraxis.axis_label_text_color = 'red'

windavgaxis = LinearAxis(y_range_name='windavg', axis_label="Wind Average")
windavgaxis.axis_label_text_color = 'green'
windgraph.add_layout(windavgaxis, 'left')
windgraph.add_layout(winddiraxis, 'left')
save(column(p, conditions, windgraph))
logger.info("Chart Written")
