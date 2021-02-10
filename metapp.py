import streamlit as st
import pandas as pd
import plotly.express as px
from modeler.core import Core

@st.cache
def load_stations():
    return Core().findstation(country='Norge')

st.title('My first app')
df = load_stations()

municipality = st.multiselect('Select municipality', pd.unique(df.municipality))
name_station = st.multiselect('Select name weather station', list(df[df.municipality == municipality[0]].name))


dfid = list(df[(df.municipality == municipality[0]) & (df.name == name_station[0])].id)

@st.cache
def load_source():
    return Core().sourceinfo(source=dfid[0],filt='temp')
df_source = load_source()

feature = st.multiselect('Select feature',list(df_source.elementId))

@st.cache
def load_features():
    return Core().graphelement(source=dfid[0], elements= feature[0],referencetime= '2020-01-01/2021-01-01',rollingmean=1)
df_features = load_features()

fig = px.line(df_features, x="referenceTime", y="value", title='Title',template="plotly_white")

st.plotly_chart(fig, use_container_width=True)

map_data = pd.DataFrame(
    geometry.coordinates,
    columns=['lat', 'lon'])

st.map(map_data)