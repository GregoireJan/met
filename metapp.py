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
# maxdate = datetime.today().date()
# mindate = (datetime.today() - timedelta(days=7)).date()
# timerange = str(mindate)+'/'+str(maxdate)

@st.cache
def load_stations():
    return Core().findstation(country='Norge')

st.sidebar.title('Met app')
df = load_stations()

ids_basic = list(pd.read_csv('ids_basic.csv',header=None,skiprows=1)[1])
df = df[df['id'].isin(ids_basic)]

print(df)

genre = st.sidebar.radio(
     "What do you want to see?",
     ('Basic', 'Exploration'))


municipality = st.sidebar.selectbox("Select municipality", sorted(pd.unique(df.municipality).astype(str)),index=92)
name_station = st.sidebar.selectbox('Select name weather station', list(df[df.municipality == municipality].name))

map_data = pd.DataFrame(
    list(df[(df.municipality == municipality) & (df.name == name_station)]["geometry.coordinates"]),
    columns=['lon', 'lat'])

dfid = list(df[(df.municipality == municipality) & (df.name == name_station)].id)

@st.cache
def load_source():
    return Core().sourceinfo(source=dfid[0])
df_source = load_source()

# mindate_airtemp = datetime.strptime(min(df_source[df_source.elementId == 'air_temperature'].validFrom),'%Y-%m-%dT%H:%M:%S.%fZ').date()
# mindate_precipi = datetime.strptime(min(df_source[df_source.elementId == 'sum(precipitation_amount P1D)'].validFrom),'%Y-%m-%dT%H:%M:%S.%fZ').date()
# try:
#     maxdate_airtemp = datetime.strptime(max(df_source[df_source.elementId == 'air_temperature'].validTo),'%Y-%m-%dT%H:%M:%S.%fZ').date()
# except:
#     maxdate_airtemp = datetime.today().date()
# try:
#     maxdate_precipi = datetime.strptime(max(df_source[df_source.elementId == 'sum(precipitation_amount P1D)'].validTo),'%Y-%m-%dT%H:%M:%S.%fZ').date()
# except:
#     maxdate_precipi = datetime.today().date()


if genre == 'Basic':
    # feature = st.sidebar.selectbox('Select feature',list(df_source.elementId))

    d1 = st.sidebar.date_input(
        "Select first date",
        (datetime.today() - timedelta(days=7*2)))
    d2 = st.sidebar.date_input(
        "Select last date",
        (datetime.today() - timedelta(days=7)).date())


    timerange=(str(d1)+'/'+str(d2))
    if (d2 - d1) < timedelta(days=14):
        elements_temp = 'air_temperature'
        elements_preci = 'sum(precipitation_amount P1D)'
    elif (d2 - d1) < timedelta(days=366*1):
        elements_temp = 'mean(air_temperature P1D)'
        elements_preci = 'sum(precipitation_amount P1D)'
    elif (d2 - d1) < timedelta(days=366*25):
        elements_temp = 'mean(air_temperature P1M)'
        elements_preci = 'sum(precipitation_amount P1M)'
    else:
        elements_temp = 'mean(air_temperature P1Y)'
        elements_preci = 'sum(precipitation_amount P1Y)'

    @st.cache
    def load_features():
        # return Core().graphelement(source=dfid[0], elements= feature,referencetime= timerange,rollingmean=1)
        air_temperature = Core().graphelement(source=dfid[0],elements= elements_temp,referencetime= timerange,rollingmean=1)
        precipitation = Core().graphelement(source=dfid[0],elements= elements_preci,referencetime= timerange,rollingmean=1)
        return air_temperature, precipitation

    df_temperature, df_precipitation = load_features()

    fig_combi = make_subplots(specs=[[{"secondary_y": True}]])#this a one cell subplot
    fig_combi.update_layout(title="Climograph",
                    template="plotly_white",title_x=0.5)

    trace1 = go.Bar(x=df_precipitation.referenceTime,
            y=df_precipitation.value, opacity=0.4,name='Precipitation')
    

    trace2 = go.Scatter(x=df_temperature.referenceTime,
            y=df_temperature.value,name='Air Temperature')

    #The first trace is referenced to the default xaxis, yaxis (ie. xaxis='x1', yaxis='y1')
    fig_combi.add_trace(trace1, secondary_y=False)

    #The second trace is referenced to xaxis='x1'(i.e. 'x1' is common for the two traces) 
    #and yaxis='y2' (the right side yaxis)

    fig_combi.add_trace(trace2, secondary_y=True)


    fig_combi.update_yaxes(#left yaxis
                    title= 'ml',showgrid= False, secondary_y=False)
    fig_combi.update_yaxes(#right yaxis
                    showgrid= True, 
                    title= '°C',
                    secondary_y=True)

    col1, col2 = st.beta_columns((2,1))

    col1.plotly_chart(fig_combi,use_container_width=True)


    @st.cache
    def load_wind():
        ws = Core().graphelement(source=dfid[0], elements= 'wind_speed',referencetime= timerange,rollingmean=1)
        ws = ws.set_index("referenceTime").resample('10T').mean().value
        wd = Core().graphelement(source=dfid[0], elements= 'wind_from_direction',referencetime= timerange,rollingmean=1)
        wd = wd.set_index("referenceTime").resample('10T').mean().value
        return ws, wd

    if (d2 - d1) < timedelta(days=31*2):
        ws, wd = load_wind()

        # ws = np.random.random(50) * 6
        # wd = np.random.randint(270,360, size=50)

        fig_rose = plt.figure()
        rect = [1,1,1,1] 
        wa = WindroseAxes(fig_rose, rect)
        fig_rose.add_axes(wa)
        wa.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
        wa.set_legend(title='Wind speed (m/s)')
        wa.set_title('Windrose')
    

        # ax = WindroseAxes.from_ax()
        # ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
        # ax.set_legend()

        # plt.savefig('windrose.png')

        # from PIL import Image
        # image = Image.open('windrose.png')

        st.set_option('deprecation.showPyplotGlobalUse', False)
        col2.pyplot(fig_rose)
        # col2.image(image,width=400)
    else:
        col2.write("Maximum time range is 2 month")

    st.map(map_data)

else:

    feature = st.sidebar.selectbox('Select feature',list(df_source.elementId))

    d1 = st.sidebar.date_input(
        "Select first date",
        (datetime.today() - timedelta(days=7*2)))
    d2 = st.sidebar.date_input(
        "Select last date",
        (datetime.today() - timedelta(days=7)).date())


    timerange=(str(d1)+'/'+str(d2))
    # if (d2 - d1) < timedelta(days=14):
    #     elements_temp = 'air_temperature'
    #     elements_preci = 'sum(precipitation_amount P1D)'
    # elif (d2 - d1) < timedelta(days=366*1):
    #     elements_temp = 'mean(air_temperature P1D)'
    #     elements_preci = 'sum(precipitation_amount P1D)'
    # elif (d2 - d1) < timedelta(days=366*25):
    #     elements_temp = 'mean(air_temperature P1M)'
    #     elements_preci = 'sum(precipitation_amount P1M)'
    # else:
    #     elements_temp = 'mean(air_temperature P1Y)'
    #     elements_preci = 'sum(precipitation_amount P1Y)'

    @st.cache
    def load_features():
        return Core().graphelement(source=dfid[0], elements= feature,referencetime= timerange,rollingmean=1)
        # air_temperature = Core().graphelement(source=dfid[0],elements= elements_temp,referencetime= timerange,rollingmean=1)
        # precipitation = Core().graphelement(source=dfid[0],elements= elements_preci,referencetime= timerange,rollingmean=1)
        # return air_temperature, precipitation

    df_feature = load_features()

    fig_combi = make_subplots(specs=[[{"secondary_y": True}]])#this a one cell subplot
    fig_combi.update_layout(title="Climograph",
                    template="plotly_white",title_x=0.5)

    # trace1 = go.Bar(x=df_feature.referenceTime,
    #         y=df_feature.value, opacity=0.4,name='Precipitation')
    

    trace2 = go.Scatter(x=df_feature.referenceTime,
            y=df_feature.value,name='Air Temperature')

    #The first trace is referenced to the default xaxis, yaxis (ie. xaxis='x1', yaxis='y1')
    fig_combi.add_trace(trace2, secondary_y=False)

    #The second trace is referenced to xaxis='x1'(i.e. 'x1' is common for the two traces) 
    #and yaxis='y2' (the right side yaxis)

    fig_combi.add_trace(trace2, secondary_y=True)


    fig_combi.update_yaxes(#left yaxis
                    title= 'ml',showgrid= False, secondary_y=False)
    fig_combi.update_yaxes(#right yaxis
                    showgrid= True, 
                    title= '°C',
                    secondary_y=True)

    # col1, col2 = st.beta_columns((2,1))

    st.plotly_chart(fig_combi,use_container_width=True)

    st.map(map_data)
