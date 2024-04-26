class PrecipColors:
    def getColor(condition):
        if condition == "Thunderstorms Possible":
            return 'red'
        elif condition == "Thunderstorms Likely":
            return 'darkred'
        elif condition == "Cloudy":
            return 'gray'
        elif condition == "Partly Cloudy":
            return 'gainsboro'
        elif condition == "Very Light Rain":
            return 'lightgoldenrodyellow'
        elif condition == "Light Rain":
            return 'palegreen'
        elif condition == "Rain Possible":
            return 'aquamarine'
        elif condition == "Rain Likely":
            return 'limegreen'
        elif condition == "Moderate Rain":
            return 'mediumseagreen'
        elif condition == "Heavy Rain":
            return 'green'
        elif condition == "Extreme Rain":
            return 'darkgreen'
        elif condition == 'Snow Possible':
            return 'aqua'
        elif condition == 'Snow Likely':
            return 'blue'
        elif condition == 'Wintery Mix Possible':
            return 'violet'
        elif condition == 'Wintery Mix Likely':
            return 'darkviolet'
        elif condition == "Clear":
            return 'white'
        else:
            raise Exception("Invalid condition received: " + condition)
