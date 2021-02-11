import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from windrose import WindroseAxes
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from modeler.core import Core

@st.cache
def load_stations():
    return Core().findstation(country='Norge')

st.title('My first app')
df = load_stations()

municipality = st.selectbox("Select municipality", sorted(pd.unique(df.municipality).astype(str)))
name_station = st.selectbox('Select name weather station', list(df[df.municipality == municipality].name))

map_data = pd.DataFrame(
    list(df[(df.municipality == municipality) & (df.name == name_station)]["geometry.coordinates"]),
    columns=['lon', 'lat'])

st.map(map_data)

dfid = list(df[(df.municipality == municipality) & (df.name == name_station)].id)

@st.cache
def load_source():
    return Core().sourceinfo(source=dfid[0],filt='temp')
df_source = load_source()

feature = st.selectbox('Select feature',list(df_source.elementId))

@st.cache
def load_features():
    return Core().graphelement(source=dfid[0], elements= feature[0],referencetime= '2020-12-01/2021-01-01',rollingmean=1)
df_features = load_features()

fig = px.line(df_features, x="referenceTime", y="value", title='Title',template="plotly_white")

st.plotly_chart(fig, use_container_width=True)

@st.cache
def load_wind():
    ws = Core().graphelement(source=dfid[0], elements= 'wind_speed',referencetime= '2020-12-01/2021-01-01',rollingmean=1)
    ws = ws.set_index("referenceTime").resample('10T').mean().value
    wd = Core().graphelement(source=dfid[0], elements= 'wind_from_direction',referencetime= '2020-12-01/2021-01-01',rollingmean=1)
    wd = wd.set_index("referenceTime").resample('10T').mean().value
    return ws, wd

ws, wd = load_wind()

ax = WindroseAxes.from_ax()
fig_rose = ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
ax.set_legend()
ax.set_xticklabels(['N', 'NW',  'W', 'SW', 'S', 'SE','E', 'NE'])
ax.set_theta_zero_location('N')

st.set_option('deprecation.showPyplotGlobalUse', False)
st.pyplot(fig_rose, use_container_width=True)