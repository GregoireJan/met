import requests
import pandas as pd
import numpy as np
from datetime import datetime 
from pandas import json_normalize
import seaborn as sns
import matplotlib.pyplot as plt

pd.options.display.max_rows = 999

# Insert your own client ID here
client_id = '68e4dc04-3f18-4f9f-8a0a-9c793d40bd79'

class Core:
    def __init__(self):
        pass

    def findstation(tr,ids=None,name=None,country=None,municipality=None,validtime=None,polygon=None,nearpoint=None):
        dflocal=pd.DataFrame([locals()]).drop(columns=["tr"])
        selec=''
        for col in dflocal.columns:
            if dflocal[col][0] != None:
                if col == 'nearpoint':
                    selec+='&geometry=nearest(POINT('+str(dflocal[col][0])+'))'
                elif col == 'polygon':
                    selec+='&geometry=POLYGON(('+str(dflocal[col][0])+'))'
                else:
                    selec+='&'+str(col)+'='+str(dflocal[col][0])
        endpoint='https://frost.met.no/sources/v0.jsonld?types=SensorSystem'+selec
        print(endpoint,'\n')
        r = requests.get(endpoint, auth=(client_id,''))
        # Extract JSON data
        json = r.json()

        # Check if the request worked, print out any errors
        if r.status_code == 200:
            data = json['data']
            print('Data retrieved from frost.met.no!\n')
            return json_normalize(data)
        else:
            print('Error! Returned status code %s' % r.status_code)
            print('Message: %s' % json['error']['message'])
            print('Reason: %s' % json['error']['reason'])

    def sourceinfo(tr,source,filt=''):
        endpoint = 'https://frost.met.no/observations/availableTimeSeries/v0.jsonld?sources='+ source
        r = requests.get(endpoint, auth=(client_id,''))
        # Extract JSON data
        json = r.json()
        # Check if the request worked, print out any errors
        row=[]
        row2=[]
        row3=[]
        elements=pd.DataFrame()
        if r.status_code == 200:
            data = json['data']
            print('Data retrieved from frost.met.no!\n')
            for i in range(len(data)):
                # if filt in data[i]['elementId']:
                row.append(data[i]['elementId'])
                row2.append(data[i]['validFrom'])
                try:
                    row3.append(data[i]['validTo'])
                except:
                    row3.append(np.nan)
            elements['elementId']=row
            elements['validFrom']=row2
            elements['validTo']=row3
        else:
            print('Error! Returned status code %s' % r.status_code)
            print('Message: %s' % json['error']['message'])
            print('Reason: %s' % json['error']['reason'])
        return elements

    def graphelement(tr,source,elements,referencetime,rollingmean=1):
        # Define endpoint and parameters
        endpoint = 'https://frost.met.no/observations/v0.jsonld'
        parameters = {
            'sources': source,
            'elements': elements,
            'referencetime': referencetime,
        }
        # Issue an HTTP GET request
        r = requests.get(endpoint, parameters, auth=(client_id,''))
        # Extract JSON data
        json = r.json()

        # Check if the request worked, print out any errors
        if r.status_code == 200:
            data = json['data']
            print('Data retrieved from frost.met.no!')

            df = pd.DataFrame()
            for i in range(len(data)):
                row = pd.DataFrame(data[i]['observations'])
                row['referenceTime'] = data[i]['referenceTime']
                row['sourceId'] = data[i]['sourceId']
                df = df.append(row)

            df = df.reset_index()[['referenceTime','value']]
            df['referenceTime'] = [datetime.strptime(each, '%Y-%m-%dT%H:%M:%S.%fZ') for each in df['referenceTime']]
            df['value']=df['value'].rolling(rollingmean).mean()

            # plt.figure(figsize=(30,10))
            # ax = sns.lineplot(x="referenceTime", y="value", data=df)

            return df

        else:
            print('Error! Returned status code %s' % r.status_code)
            print('Message: %s' % json['error']['message'])
            print('Reason: %s' % json['error']['reason'])

# print(Core().findstation(country='Norge'))
# print(Core().findstation(ids='SN741200'))
# pd.unique(Core().findstation(country='Norge').municipality)