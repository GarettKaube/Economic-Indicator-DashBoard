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
