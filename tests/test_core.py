import pytest
from datetime import datetime, timedelta
from modeler.core import Core


# Compupte time range and select appropriate feature accordingly
timerange=(str((datetime.today() - timedelta(days=7)).date())+'/'+str((datetime.today() - timedelta(days=1)).date()))

def test_stations():
    df = Core().findstation(country='Norge')
    assert len(df) > 0

def test_sources():
    df = Core().sourceinfo(source='SN18700')
    assert len(df) > 0

def test_features():
    air_temperature = Core().graphelement(source='SN18700',elements= 'air_temperature',referencetime= timerange,rollingmean=1)
    assert len(air_temperature) > 0