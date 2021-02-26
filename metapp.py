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
import math
from modeler.core import Core


st.set_page_config(layout="wide")

hide_streamlit_style = """
            <style>
            footer:after {
                content:'by https://gregoirejan.github.io / Using frost.met.no API'; 
                visibility: visible;
                display: block;
                position: relative;
                #background-color: red;
                padding: 5px;
                top: 2px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

##############################################################################################################################################
st.sidebar.title('Norwegian Meteorological app')


# Load stations list in Norway
@st.cache
def load_stations():
    return Core().findstation(country='Norge')
df = load_stations()

# Filter list by selecting only statoins with air temp + precipitations + wind speed/directoin
ids_basic = list(pd.read_csv('ids_basic_nonan.csv',header=None,skiprows=1)[1])
df_basic = df[df['id'].isin(ids_basic)]

# Select between Basic features viz or Exploration
genre = st.sidebar.radio(
     "What do you want to see?",
     ('Basic features', 'Exploration mode'))

if genre == 'Basic features':

    # Select Municipality and station
    municipality = st.sidebar.selectbox("Select municipality", sorted(pd.unique(df_basic.municipality).astype(str)),index=52)
    name_station = st.sidebar.selectbox('Select weather station', list(df_basic[df_basic.municipality == municipality].name))

    # Prepare map data
    map_data = pd.DataFrame(
        list(df_basic[(df_basic.municipality == municipality) & (df_basic.name == name_station)]["geometry.coordinates"]),
        columns=['lon', 'lat'])

    # Get id for selected station
    dfid = list(df_basic[(df_basic.municipality == municipality) & (df_basic.name == name_station)].id)

    # Get source info about the selected station
    @st.cache
    def load_source():
        return Core().sourceinfo(source=dfid[0])
    df_source = load_source()

    # Select time range
    d1 = st.sidebar.date_input(
        "Select first date",
        (datetime.today() - timedelta(days=7)))
    d2 = st.sidebar.date_input(
        "Select last date",
        (datetime.today() - timedelta(days=1)).date())

    # Compupte time range and select appropriate feature accordingly
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

    # Get data for the selected station / feature / time range
    @st.cache
    def load_features():
        air_temperature = Core().graphelement(source=dfid[0],elements= elements_temp,referencetime= timerange,rollingmean=1)
        precipitation = Core().graphelement(source=dfid[0],elements= elements_preci,referencetime= timerange,rollingmean=1)
        return air_temperature, precipitation

    # Insert value when temperature crossess 0 in order to get blue/red coloring
    df_temperature, df_precipitation = load_features()
    df_temperature_positive = df_temperature.copy()
    df_temperature_positive.loc[df_temperature_positive.value <= 0, 'value'] = np.nan
    df_temperature_negative = df_temperature.copy()
    df_temperature_negative.loc[df_temperature_negative.value > 0, 'value'] = np.nan

    df_temperature_positive = df_temperature_positive.set_index('referenceTime')
    df_temperature_negative = df_temperature_negative.set_index('referenceTime')
    df_precipitation = df_precipitation.set_index('referenceTime')

    idxp = [i for i in range(1,len(df_temperature_positive)) if math.isnan(df_temperature_positive.iloc[i,0]) and not math.isnan(df_temperature_positive.iloc[i-1,0])]
    idxn = [i for i in range(0,len(df_temperature_positive)-1) if math.isnan(df_temperature_positive.iloc[i,0]) and not math.isnan(df_temperature_positive.iloc[i+1,0])]
    idxts = [df_temperature_positive.index[i-1]+(df_temperature_positive.index[i]-df_temperature_positive.index[i-1])/2 for i in pd.unique(idxp)] + [df_temperature_positive.index[i]+(df_temperature_positive.index[i+1]-df_temperature_positive.index[i])/2 for i in pd.unique(idxn)]
    zeros = pd.DataFrame([0]*len(idxts),columns=['value'],index=idxts)
    df_temperature_positive = df_temperature_positive.append(zeros).sort_index()
    df_temperature_negative = df_temperature_negative.append(zeros).sort_index()

    # Prepare plot for temperature and precipitations
    fig_combi = make_subplots(specs=[[{"secondary_y": True}]])#this a one cell subplot
    fig_combi.update_layout(title="Climograph",
                    template="plotly_white",title_x=0.5,legend=dict(orientation='h'))

    trace1 = go.Bar(x=df_precipitation.index,
            y=df_precipitation.value, opacity=0.4,name='Precipitation')
    
    trace2p = go.Scatter(x=df_temperature_positive.index,
            y=df_temperature_positive.value,name='Air Temperature (positive)',mode='lines',line=dict(color='red', width=1))
    trace2n = go.Scatter(x=df_temperature_negative.index,
            y=df_temperature_negative.value,name='Air Temperature (negative)',mode='lines',line=dict(color='blue', width=1))

    #The first trace is referenced to the default xaxis, yaxis (ie. xaxis='x1', yaxis='y1')
    fig_combi.add_trace(trace1, secondary_y=False)

    #The second trace is referenced to xaxis='x1'(i.e. 'x1' is common for the two traces) 
    #and yaxis='y2' (the right side yaxis)

    fig_combi.add_trace(trace2p, secondary_y=True)
    fig_combi.add_trace(trace2n, secondary_y=True)

    fig_combi.update_yaxes(#left yaxis
                    title= 'ml',showgrid= False, secondary_y=False)
    fig_combi.update_yaxes(#right yaxis
                    showgrid= True, 
                    title= '°C',
                    secondary_y=True)

    # Load wind data
    @st.cache
    def load_wind():
        ws = Core().graphelement(source=dfid[0], elements= 'wind_speed',referencetime= timerange,rollingmean=1)
        ws = ws.set_index("referenceTime").resample('10T').mean().value
        wd = Core().graphelement(source=dfid[0], elements= 'wind_from_direction',referencetime= timerange,rollingmean=1)
        wd = wd.set_index("referenceTime").resample('10T').mean().value
        return ws, wd

    # Layout accordingly if windrose is plotted (timerange < 2 month)
    if (d2 - d1) < timedelta(days=31*2):

        # Plot temp and precipitations
        col1, col2 = st.beta_columns((2,1))

        # Previous years comparison
        year_comparison = st.sidebar.text_input('Compare current temperatures/precipitations to previous years (e.g. type 4 for 4 years back):', 'None')

        if (year_comparison != 'None') and (year_comparison != 'none') :
            year_comparison = int(year_comparison)
            timerange_comp=(str(d1.replace(year=d1.year-year_comparison))+'/'+str(d2.replace(year=d1.year-year_comparison)))

            @st.cache
            def load_features_comp():
                air_temperature_comp = Core().graphelement(source=dfid[0],elements= elements_temp,referencetime= timerange_comp,rollingmean=1)
                precipitation_comp = Core().graphelement(source=dfid[0],elements= elements_preci,referencetime= timerange_comp,rollingmean=1)
                return air_temperature_comp, precipitation_comp

            df_temperature_comp, df_precipitation_comp = load_features_comp()
            df_temperature_comp = df_temperature_comp.set_index('referenceTime')
            df_precipitation_comp = df_precipitation_comp.set_index('referenceTime')
            df_temperature_comp.index = df_temperature_comp.index + pd.offsets.DateOffset(years=year_comparison)
            df_precipitation_comp.index = df_precipitation_comp.index + pd.offsets.DateOffset(years=year_comparison)
            trace2c = go.Scatter(x=df_temperature_comp.index,
                y=df_temperature_comp.value,name='Air Temperature (comparison)',mode='lines',line=dict(color='black', width=1),opacity=0.15,hovertemplate='(%{text}, %{y})',text=load_features_comp()[0].set_index('referenceTime').index.strftime("%b %d, %Y, %H:%M"))
            fig_combi.add_trace(trace2c, secondary_y=True)
            trace1c = go.Bar(x=df_precipitation_comp.index,y=df_precipitation_comp.value, marker_color='lightblue', opacity=0.25,name='Precipitation (comparison)',hovertemplate='(%{text}, %{y})',text=load_features_comp()[1].set_index('referenceTime').index.strftime("%b %d, %Y"))
            fig_combi.add_trace(trace1c, secondary_y=False)

        col1.plotly_chart(fig_combi,use_container_width=True)


        # Windrose plot
        ws, wd = load_wind()

        fig_rose = plt.figure()
        rect = [1,1,1,1] 
        wa = WindroseAxes(fig_rose, rect)
        fig_rose.add_axes(wa)
        wa.bar(wd, ws, normed=True, opening=0.8, edgecolor='white')
        wa.set_legend(title='Wind speed (m/s)')
        wa.set_title('Windrose')

        st.set_option('deprecation.showPyplotGlobalUse', False)
        col2.pyplot(fig_rose)
    else:
        # Plot only temp and precipitations
        st.error("Maximum time range for the Windrose and comparison is 2 month.")
        st.plotly_chart(fig_combi,use_container_width=True)

    # Plot map
    st.map(map_data)

else:

    try:
        # Select Municipality and station
        municipality = st.sidebar.selectbox("Select municipality", sorted(pd.unique(df.municipality).astype(str)))
        name_station = st.sidebar.selectbox('Select name weather station', list(df[df.municipality == municipality].name))

        # Map data
        map_data = pd.DataFrame(
            list(df[(df.municipality == municipality) & (df.name == name_station)]["geometry.coordinates"]),
            columns=['lon', 'lat'])

        # Get station id
        dfid = list(df[(df.municipality == municipality) & (df.name == name_station)].id)
        
        # Load data
        @st.cache
        def load_source():
            return Core().sourceinfo(source=dfid[0])
        df_source = load_source()

        # Select feature to plot
        feature = st.sidebar.selectbox('Select feature',list(df_source.elementId),index=1)

        #Select time range
        d1 = st.sidebar.date_input(
            "Select first date",
            (datetime.today() - timedelta(days=7)))
        d2 = st.sidebar.date_input(
            "Select last date",
            (datetime.today() - timedelta(days=1)).date())
        timerange=(str(d1)+'/'+str(d2))

        # Load data for selected station / feature / time range
        @st.cache
        def load_features():
            return Core().graphelement(source=dfid[0], elements= feature,referencetime= timerange,rollingmean=1)
        df_feature = load_features()

        # Prepare plot
        fig = go.Figure(data=go.Scatter(x=df_feature.referenceTime,y=df_feature.value,name=str(feature),mode='lines',line=dict(color='red', width=1)))
        fig.update_layout(title=str(feature),
                        template="plotly_white",title_x=0.5,legend=dict(orientation='h'))

        # Plot feature
        st.plotly_chart(fig,use_container_width=True)
        # Plot map
        st.map(map_data)

    except:
        # Error if not avaiblable
        st.error('Please select another feature or another time range')
        st.write('Available time range: ', min(df_source[df_source.elementId == feature].validFrom.fillna(datetime.today())),' to ',max(df_source[df_source.elementId == feature].validTo.fillna(datetime.today())))