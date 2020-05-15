import os
import json
from flask import Flask, request
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import geohash
import re


app = Flask(__name__)

@app.route('/api/uv')
def get_uv_data():
    date = requests.args.get('date')
    response = urlopen('ftp://ftp2.bom.gov.au/anon/gen/fwo/IDZ00112.xml')
    soup = BeautifulSoup(response, 'xml')

    melb = soup.find_all('area', description='Melbourne')[0]
    melb_forecasts = melb.find_all('forecast-period')
    
    uvforecasts = []
    for f in melb_forecasts:
        prot_time = re.search(r'(?<=recommended from ).*(?=, UV Index)', f.find('text').get_text())
        prot_time = None if prot_time is None else prot_time[0].split(' to ')
        uvforecasts.append({
            "n": f['index'],
            "date_start": f['start-time-local'],
            "date_end": f['end-time-local'],
            "max_level": re.search(r'(?<= UV Index predicted to reach )\d', f.find('text').get_text())[0],
            "protection_times": None if prot_time is None else (prot_time[0], prot_time[1])
        })

    params = {
        'longitude':'145.1',
        'latitude': '-37.73',
        'date': date
    }

    currUVReq = requests.get('https://uvdata.arpansa.gov.au/api/uvlevel', params=params)
    # print(type(response))
    currUvRes = currUVReq.json()
    currUvRes.pop('GraphData', None)
    response = {
        'current': currUvRes,
        'forecast': uvforecasts
    }
    return json.dumps(response)



@app.route('/api/3hourly')
def threehourly():
    coords = {
        'lat': float(request.args.get('lat')),
        'long': float(request.args.get('long'))
    }
    hashgeo = geohash.encode(coords['lat'], coords['long'])[:6]
    forecast = requests.get(f'https://api.weather.bom.gov.au/v1/locations/{hashgeo}/forecasts/3-hourly')

    return forecast.json()
    # return json.dumps(forecast.json())


@app.route('/api/daily')
def daily():
    coords = {
        'lat': float(request.args.get('lat')),
        'long': float(request.args.get('long'))
    }
    hashgeo = geohash.encode(coords['lat'], coords['long'])[:6]
    forecast = requests.get(f'https://api.weather.bom.gov.au/v1/locations/{hashgeo}/forecasts/daily')

    return forecast.json()
    # return json.dumps(forecast.json())



# return app
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)