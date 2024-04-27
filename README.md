# tempestGraph
These programs utilize the Bokeh library to generate graphs from the data collected from the Tempest API.  The Forecast data is taken from the Tempest REST API https://apidocs.tempestwx.com/reference/get_better-forecast.  The local observation data is collected from the Tempest Websocket integration https://apidocs.tempestwx.com/reference/websocket-reference

To run these programs, you'll need to get your station id and an access token, information on obtaining these can be found here https://weatherflow.github.io/Tempest/api/

You'll also need to install the Bokeh Python library.  Here is a getting started guide https://docs.bokeh.org/en/latest/docs/first_steps.html  If you are new to Python, here is a good place to start https://www.python.org/about/gettingstarted/

You should be able to run these programs as is by simply updating the renaming the sample.env file to .env and updating the values in it for your Tempest station. 

You can view the files these programs create in any web browser on your local workstation, simply type in the path to the file into your webbrowser 'Desktop/myfiles/forecast.html' but I have it setup with a webserver so that I can access the files from any place on my network.  If you would like to go this route, you'll need to setup and run a webserver.  I use Apache https://httpd.apache.org/docs/trunk/getting-started.html
