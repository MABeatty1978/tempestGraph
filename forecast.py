#!/usr/bin/python3

import requests
import logging
import os
import argparse
from precipcolors import PrecipColors
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import column
from bokeh.models import Range1d, LinearAxis, ColumnDataSource, Legend, DatetimeTickFormatter
from bokeh.io import export_png
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
dayXaxis=[]
temp=[]
feelslike=[]
uv=[]
humidity=[]
windgust=[]
windavg=[]
winddir=[]
windday=[]
winddirday=[]
precipchance=[]
precipchanceDay=[]
baro=[]
condColor=[]
conditions=[]
conditionsDay=[]
precip=[]
tempDay=[]
condColorDay=[]

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

#Connect to API
logger.info("Connecting to WeatherFlow")
URL = "https://swd.weatherflow.com/swd/rest/better_forecast?station_id={}&units_pressure=inhg&units_temp=f&units_wind=mph&units_precip=in&units_distance=mi&token={}".format(station, token)
logger.debug("URL: " + URL)

r = requests.get(url = URL)
rc = r.status_code
if rc != 200:
    logger.error("Connection returned with status code: " + str(rc))
    quit()
logger.info("Data received")
d = r.json()

#Variables and logic to handle rolling the month
month = datetime.now().month
year = datetime.now().year
startday = d['forecast']['hourly'][0]['local_day']
monthrolled=False

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
    conditions.append(f['conditions'])
    windgust.append(f['wind_gust'])
    windavg.append(f['wind_avg'])
    winddir.append(f['wind_direction'])
    baro.append(f['sea_level_pressure'])
    precip.append(f['precip'])
    humidity.append(f['relative_humidity'])
    feelslike.append(f['feels_like'])
    uv.append(f['uv'])
    try:
        condColor.append(PrecipColors.getColor(f['conditions']))
    except Exception as e:
        logger.warning(e)
        condColor.append('black')
#24 hour forecast
for i in range(0,23):
    conditionsDay.append(conditions[i])
    tempDay.append(temp[i])
    dayXaxis.append(xAxis[i])
    precipchanceDay.append(precipchance[i])
    windday.append(windgust[i])
    winddirday.append(winddir[i])
    try:
        condColorDay.append(PrecipColors.getColor(conditions[i]))
    except Exception as e:
        logger.warning(e)
        condColorDay.append('black')


output_file(filename=fname, title="10 Day Hourly Forecast")
temps = figure(title="Forecast " + str(datetime.now()), width=1500, x_axis_type='datetime')
#Temp
temps.line(y=temp, x=xAxis, line_color='blue', legend_label="Temperature")
temps.yaxis.axis_label = 'Degrees'
temps.xaxis.ticker.desired_num_ticks =72 
temps.xaxis.major_label_orientation = 'vertical' 
#Feels Like
temps.line(x=xAxis, y=feelslike, line_color='green', legend_label="Feels Like")

hpu = figure(title="Humidity, Pressure, and UV", y_axis_label='InHg', width=1500, x_axis_type='datetime')
hpu.yaxis.axis_label_text_color = 'green'
hpu.y_range = Range1d(min(baro)-.1, max(baro)+.1)
hpu.extra_y_ranges['humidity'] = Range1d(0,100)
hpu.extra_y_ranges['uv'] = Range1d(0,max(uv))
hpu.line(y=baro, x=xAxis, line_color='green')

hpu.line(x=xAxis, y=uv, y_range_name='uv', line_color='red')
ax4 = LinearAxis(y_range_name='uv', axis_label="UV")
ax4.axis_label_text_color='red'
hpu.add_layout(ax4, 'left')

hpu.line(x=xAxis, y=humidity, y_range_name='humidity', line_color='black')
ax5 = LinearAxis(y_range_name='humidity', axis_label='Humidity')
ax5.axis_label_text_color='black'
hpu.add_layout(ax5, 'left')

source = ColumnDataSource(dict(x=xAxis, y=precipchance, color=condColor, label=conditions))

conditions = figure(title="10 Day Hourly Forecast", width=1500, x_axis_type='datetime')
conditions.extra_y_ranges['precip'] = Range1d(0, max(precip))
conditions.y_range = Range1d(0, 100)
conditions.yaxis.axis_label="Chance of Precipitation/Type"
conditions.vbar(x='x', top='y', color='color', legend_group='label', source = source, width=.5, line_width=5)
conditions.line(x=xAxis, y=precip, y_range_name='precip', color='blue')
conditionsax2 = LinearAxis(y_range_name='precip', axis_label="Rain Rate Per Hour")
conditionsax2.axis_label_text_color='blue'
conditions.add_layout(conditionsax2, 'left')
conditions.xaxis.ticker.desired_num_ticks=72
conditions.xaxis.major_label_orientation = 'vertical'

sourceDay = ColumnDataSource(dict(x=dayXaxis, y=precipchanceDay, color=condColorDay, label=conditionsDay))
conditionsDay = figure(title="24 Hour Forecast " + str(datetime.now()), width=1000, x_axis_type='datetime')
conditionsDay.extra_y_ranges['tempDay'] = Range1d(min(tempDay)-5, max(tempDay)+5)
conditionsDay.extra_y_ranges['windSpeed'] = Range1d(0, max(windday)+5)
conditionsDay.extra_y_ranges['windDir'] = Range1d(0, 365)
conditionsDay.y_range = Range1d(0, 100)
conditionsDay.yaxis.axis_label="Chance of Precipitation/Type"
conditionsDay.vbar(x='x', top='y', color='color', legend_group='label', source=sourceDay, line_width=20)
conditionsDay.line(x=dayXaxis, y=tempDay, y_range_name='tempDay', color='blue')
conditionsDayax2 = LinearAxis(y_range_name='tempDay', axis_label="Temperature")
conditionsDayax2.axis_label_text_color='blue'
conditionsDayGust = LinearAxis(y_range_name='windSpeed', axis_label="Wind Gust")
conditionsDayGust.axis_label_text_color='red'
conditionsDayDir = LinearAxis(y_range_name='windDir', axis_label="Wind Direction (degrees)")
conditionsDayDir.axis_label_text_color='red'
conditionsDay.line(x=dayXaxis, y=windday, y_range_name='windSpeed', color='red')
conditionsDay.scatter(x=dayXaxis, y=winddirday, y_range_name='windDir', color='red')
conditionsDay.add_layout(conditionsDayax2, 'left')
conditionsDay.add_layout(conditionsDayGust, 'right')
conditionsDay.add_layout(conditionsDayDir, 'right')
conditionsDay.xaxis.ticker.desired_num_ticks=24
conditionsDay.xaxis.major_label_orientation = 'vertical'
conditionsDay.xaxis.formatter=DatetimeTickFormatter(hours="%l %P")
conditionsDay.legend.glyph_width = 1
conditionsDay.legend.glyph_height = 1
conditionsDay.legend.label_standoff=25

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
save(column(temps, conditions, conditionsDay, windgraph, hpu))
logger.info("Chart written")
export_png(temps, filename=server+"temps.png")
logger.info("temps.png written")
export_png(conditions, filename=server+"forecastg.png")
logger.info("forecastg.png written")
export_png(windgraph, filename=server+"winds.png")
logger.info("winds.png written")
export_png(hpu, filename=server+"hpu.png")
logger.info("hpu.png written")
export_png(conditionsDay, filename=server+"conditionsDay.png")
logger.info("conditionsDay.png written")
