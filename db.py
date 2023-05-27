import numpy as np
import pandas as pd
from fredapi import Fred
import streamlit as st
from utils import *
import pickle


# innitialization
API_KEY = '####'
fred = Fred(api_key=API_KEY)
series_header_size = 6


def add_to_class(Class): #@save
    def wrapper(obj):
        setattr(Class, obj.__name__, obj)
    return wrapper


class Data:
    def __init__(self, series:str, name:str, start, period:int):
        self.series = series
        self.name = name
        
        self.period = period
        self.percent_chg = None

        try:
            data = fred.get_series(self.series)
        except Exception:
            pass

        else:
            data = data[data.index >= start]
            self.data = add_names(data, self.name)
        if self.period == None:
             self.infer_freq()
             

@add_to_class(Data)
def write_data(self, chart_type = 'line'):
        st.write("""
        {} {}
        """.format('#'*series_header_size, self.name))
        if chart_type =='line':
            st.line_chart(self.data)

        elif chart_type == 'area':
            st.area_chart(self.data)


@add_to_class(Data)
def write_latest_vals(self,n=4):
        latest = display_most_recent(self.data, n)
        st.write("""
        ##### LATEST {} Values
            """.format(self.name))
        st.write(latest)


@add_to_class(Data)
def get_series(self):
     return self.data


@add_to_class(Data)
def calculate_pct_chg(self):
     self.percent_chg = ((self.data.diff(self.period)/ self.data.abs().shift(self.period))*100).dropna()
     
     st.write("""
        {} Percent Change for {}
     """.format('#'*series_header_size, self.name))
     
     st.line_chart(self.percent_chg)



st.sidebar.header('Economic Indicator Selection')



# Dictrionary that is of the form: "Series name": ["Fred Code", Period]
with open('saved_series.pkl', 'rb') as f:
    fred_dict = pickle.load(f)

@add_to_class(Data)
def infer_freq(self):
     freq = pd.infer_freq(self.data.index)
     if freq == "QS-OCT":
          self.period = 4
     else:
          self.period = 1


selected_indicators = st.sidebar.multiselect('Indicator', fred_dict.keys())
with st.sidebar:
    with st.form('FREDData'):
        new_data = st.text_input("Add FRED Data","FRED CODE")
        name_of_series = st.text_input("Name of data","Enter Name")
        submitted = st.form_submit_button("ADD")
        if submitted:
            fred_dict[name_of_series] = [new_data, None]
            with open('saved_series.pkl', 'wb') as f:
                pickle.dump(fred_dict, f)



tab1, tab2 = st.tabs(['Time-Series', 'Percent Change'])

start = pd.Timestamp(2014,1,1)
series_objects = []    # store series (Data) objects 


with tab1:
    chart_type = st.selectbox('Chart Type', ('line', 'area'))

    num_indicators = len(selected_indicators)
    if num_indicators == 0:
        columns = st.columns(1, gap = 'medium')
        n_cols=1
    elif num_indicators >= 2:
        columns = st.columns(2, gap = 'medium')
        n_cols = 2
    else:
        columns = st.columns(1, gap = 'medium')
        n_cols = 1

    # make series objects and display time plots of selected series
    for i, ind in enumerate(selected_indicators):
        
            with columns[i%n_cols]:
                series = Data(fred_dict[ind][0], ind, start, fred_dict[ind][1])
                series_objects.append(series)
                series.write_data(chart_type)


selected_indicators_for_pct = selected_indicators.copy()
try:
    selected_indicators_for_pct.remove("10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity")
except ValueError:
    pass

# calculate and display percentage change of selected time series on second tab
with tab2:
    num_indicators_for_pct = len(selected_indicators_for_pct)

    if num_indicators >= 2:
        columns_pct = st.columns(2, gap = 'medium')
        n_cols_pct = 2
    else:
        columns_pct = st.columns(1, gap = 'medium')
        n_cols_pct = 1

    for i,s in enumerate(series_objects):
        with columns_pct[i%n_cols_pct]:
            if s.name in selected_indicators_for_pct:
                s.calculate_pct_chg()




