import os
import json
from flask import Flask, request
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

def get_uv_data(date):
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

    print(date)
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
    return response

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route('/')
    def hello():
        print("recieved request")
        print()
        return json.dumps(get_uv_data(request.args.get('date')))
    
    return app