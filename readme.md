# Norwegian MET app

My Norwegian Meteoroligical app is an app to help any meteorological enthousiast to visualise the available weather data from MET using its [Frost](https://frost.met.no/) API. The app is powered by [Streamlit](streamlit.io).

## Directory structure

* modeler/: contest Python class calling the Frost API and preping the data
* test/: contains test script running pytest 
* metapp.py: contains the streamlit app

## Running locally

* Clone repo
* Install steamlit & requirements
```
pip install streamlit
pip install -r requirements.txt 
```
* Run streamlit
```
streamlit run metapp.py
```