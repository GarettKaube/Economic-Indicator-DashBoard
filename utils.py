import numpy as np
import pandas as pd
from fredapi import Fred
import streamlit as st

def add_names(series, series_name:str):
    series.name = series_name
    series.index.name = 'Date'
    return series



def correlate(df1, df2):
    df1 = df1.to_frame().reset_index(drop=False)
    df2 = df2.to_frame().reset_index(drop=False)
    merged = df1.merge(df2, on='Date').drop('Date', axis=1).dropna()
    corre = merged.corr()
   
    return corre



def add_to_class(Class): #@save
    def wrapper(obj):
        setattr(Class, obj.__name__, obj)
    return wrapper


def get_tabs(num_indicators):
    """
    Creates tabs based on the number of time-series selected
    returns: time_series_tab, percent_change_tab, data_tab, summary_tab, which are all streamlit tab objects
    """
    time_series_tab = None
    percent_change_tab = None
    data_tab = None
    summary_tab = None

    if num_indicators > 1:
        time_series_tab, percent_change_tab, data_tab, summary_tab = st.tabs(['Time-Series', 'Percent Change', 'Data', 'Summary'])
        
    elif  num_indicators == 1:
        time_series_tab, percent_change_tab, data_tab = st.tabs(['Time-Series', 'Percent Change', 'Data'])
        
    else:
        st.text_area(label="Get Started", value = "Select a time series on the left", height=30, key='get_startedd')
    
    return time_series_tab, percent_change_tab, data_tab, summary_tab
