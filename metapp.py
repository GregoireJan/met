import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from windrose import WindroseAxes
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from datetime import datetime, timedelta, date, time
from modeler.core import Core

st.set_page_config(layout="wide")
maxdate = datetime.today().date()
mindate = (datetime.today() - timedelta(days=7)).date()
timerange = str(mindate)+'/'+str(maxdate)

@st.cache
def load_stations():
    return Core().findstation(country='Norge')

st.sidebar.title('Met app')
df = load_stations()


municipality = st.sidebar.selectbox("Select municipality", sorted(pd.unique(df.municipality).astype(str)),index=213)
name_station = st.sidebar.selectbox('Select name weather station', list(df[df.municipality == municipality].name),index=1)

map_data = pd.DataFrame(
    list(df[(df.municipality == municipality) & (df.name == name_station)]["geometry.coordinates"]),
    columns=['lon', 'lat'])

dfid = list(df[(df.municipality == municipality) & (df.name == name_station)].id)

@st.cache
def load_source():
    return Core().sourceinfo(source=dfid[0])
df_source = load_source()

mindate_airtemp = datetime.strptime(min(df_source[df_source.elementId == 'air_temperature'].validFrom),'%Y-%m-%dT%H:%M:%S.%fZ').date()
mindate_precipi = datetime.strptime(min(df_source[df_source.elementId == 'sum(precipitation_amount P1D)'].validFrom),'%Y-%m-%dT%H:%M:%S.%fZ').date()
try:
    maxdate_airtemp = datetime.strptime(max(df_source[df_source.elementId == 'air_temperature'].validTo),'%Y-%m-%dT%H:%M:%S.%fZ').date()
except:
    maxdate_airtemp = datetime.today().date()
try:
    maxdate_precipi = datetime.strptime(max(df_source[df_source.elementId == 'sum(precipitation_amount P1D)'].validTo),'%Y-%m-%dT%H:%M:%S.%fZ').date()
except:
    maxdate_precipi = datetime.today().date()

feature = st.sidebar.selectbox('Select feature',list(df_source.elementId),index=13)

st.sidebar.map(map_data)

# appointment = st.slider(
#      "Schedule your appointment:",min_value=max(mindate_airtemp,mindate_precipi),max_value=min(maxdate_airtemp,maxdate_precipi),
#      value=(datetime.today().date(),datetime.today().date()))
# st.write("You're scheduled for:", appointment)

d1 = st.date_input(
    "When's your birthday",
    date(2021, 1, 1))
d2 = st.date_input(
    "When's your birthday",
    date(2021, 1, 31))

timerange=(str(d1)+'/'+str(d2))
if (d2 - d1) < timedelta(days=14):
    elements_temp = 'air_temperature'
    elements_preci = 'sum(precipitation_amount P1D)'
    rolling = 1
elif (d2 - d1) < timedelta(days=366):
    elements_temp = 'mean(air_temperature P1D)'
    elements_preci = 'sum(precipitation_amount P1D)'
    rolling = 14
elif (d2 - d1) < timedelta(days=366*10):
    elements_temp = 'mean(air_temperature P1M)'
    elements_preci = 'sum(precipitation_amount P1M)'
else:
    elements_temp = 'mean(air_temperature P1Y)'
    elements_preci = 'sum(precipitation_amount P1Y)'

@st.cache
def load_features():
    # return Core().graphelement(source=dfid[0], elements= feature,referencetime= timerange,rollingmean=1)
    air_temperature = Core().graphelement(source=dfid[0],elements= elements_temp,referencetime= timerange,rollingmean=rolling)
    precipitation = Core().graphelement(source=dfid[0],elements= elements_preci,referencetime= timerange,rollingmean=1)
    return air_temperature, precipitation

df_temperature, df_precipitation = load_features()

# col1, col2 = st.beta_columns(2)

# fig_temperature = px.line(df_temperature, x="referenceTime", y="value", title='Title',template="plotly_white")
# col1.plotly_chart(fig_temperature,use_container_width=True)
# fig_precipitation = px.bar(df_precipitation, x="referenceTime", y="value", title='Title',template="plotly_white")
# fig_precipitation.update_xaxes(ticklabelposition='outside left')
# col1.plotly_chart(fig_precipitation,use_container_width=True)


fig_combi = make_subplots(specs=[[{"secondary_y": True}]])#this a one cell subplot
fig_combi.update_layout(title="Figure Title",
                  template="plotly_white")

trace1 = go.Bar(x=df_precipitation.referenceTime,
        y=df_precipitation.value)
 

trace2 = go.Scatter(x=df_temperature.referenceTime,
        y=df_temperature.value)

#The first trace is referenced to the default xaxis, yaxis (ie. xaxis='x1', yaxis='y1')
fig_combi.add_trace(trace1, secondary_y=False)

#The second trace is referenced to xaxis='x1'(i.e. 'x1' is common for the two traces) 
#and yaxis='y2' (the right side yaxis)

fig_combi.add_trace(trace2, secondary_y=True)


fig_combi.update_yaxes(#left yaxis
                 title= 'Cumulative precipitation',showgrid= False, secondary_y=False)
fig_combi.update_yaxes(#right yaxis
                 showgrid= True, 
                 title= 'Temperature',
                 secondary_y=True)

st.plotly_chart(fig_combi,use_container_width=True)


# @st.cache
# def load_wind():
#     ws = Core().graphelement(source=dfid[0], elements= 'wind_speed',referencetime= timerange,rollingmean=1)
#     ws = ws.set_index("referenceTime").resample('10T').mean().value
#     wd = Core().graphelement(source=dfid[0], elements= 'wind_from_direction',referencetime= timerange,rollingmean=1)
#     wd = wd.set_index("referenceTime").resample('10T').mean().value
#     return ws, wd

# ws, wd = load_wind()

# ax = WindroseAxes.from_ax()
# fig_rose = ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
# ax.set_legend()
# ax.set_xticklabels(['N', 'NW',  'W', 'SW', 'S', 'SE','E', 'NE'])
# ax.set_theta_zero_location('N')

# st.set_option('deprecation.showPyplotGlobalUse', False)
# col2.pyplot(fig_rose)