import numpy as np
import pandas as pd
from fredapi import Fred
import streamlit as st
from utils import *
import pickle
import datetime

st.set_page_config(layout="wide")

# innitialization
API_KEY = '9a048a276f1a939a1e64c77f214e5684'
fred = Fred(api_key=API_KEY)
series_header_size = 6


def add_to_class(Class): #@save
    def wrapper(obj):
        setattr(Class, obj.__name__, obj)
    return wrapper


class Data:
    def __init__(self, series:str, name:str, start, period:int, end, annual = None):
        self.series = series
        self.name = name
        
        self.start = start
        self.end = end

        self.period = period
        self.percent_chg = None
        self.annual = annual

        self.data = None
        self.last_vals = None

    
@add_to_class(Data)
def get_data(self):
    try:
        data = fred.get_series(self.series)
    except Exception:
        pass
    else:
        self.data = add_names(data, self.name)
        if self.period == None:
            self.infer_freq()
        self.last_vals = self.data.tail(4)
        



@add_to_class(Data)
def write_data(self, chart_type = 'line'):
        st.write("""
        {} {}
        """.format('#'*series_header_size, self.name))
        
        data_filtered = self.data[(self.data.index >= self.start) & (self.data.index <= self.end)]
        # Handeling the case of a small time frame selection causing some series of small frequency not plotting
        if data_filtered.size > 10:
            if chart_type =='line':
                st.line_chart(self.data)

            elif chart_type == 'area':
                st.area_chart(self.data.fillna(method='ffill'))
        
        # if series is small plot the 4 last observed values
        elif self.last_vals is not None and data_filtered.size > 1:
            if chart_type =='line':
                st.line_chart(data_filtered)

            elif chart_type == 'area':
                st.area_chart(data_filtered.fillna(method='ffill'))
        
        else:
            st.bar_chart(self.last_vals.tail(2))


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
     period = self.period * 12 if self.annual == True else self.period

     self.percent_chg = ((self.data.diff(period)/ self.data.abs().shift(period))*100).dropna()
     
     percent_chg_filtered = self.percent_chg[(self.percent_chg.index <= self.end) & (self.percent_chg.index >= self.start)]
     st.write("""
        {} Percent Change for {}
     """.format('#'*series_header_size, self.name))
     if percent_chg_filtered.size > 1:
       
        st.line_chart(percent_chg_filtered)
     else:
         st.write("""### Not enough data to calculate percent change""")


st.sidebar.header('Economic Indicator Selection')


# Dictionary that is of the form: "Series name": ["Fred Code", Period]
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

# Time frame selection
with st.sidebar:
    start_select = st.date_input('Start of Time Series', min_value=datetime.date(1950,1,1), value =datetime.date(2014,1,1))
    start = pd.Timestamp(start_select.year, start_select.month, start_select.day)

    end_select = st.date_input('End of Time Series',min_value=datetime.date(1950,1,1) )
    end = pd.Timestamp(end_select.year, end_select.month, end_select.day)

    # make sure the start date is before the end date
    try:
        assert end >= start
    except AssertionError:
        st.markdown(":red[Start should be before end date!]")
        stop = True
    else:
        stop = False


# Get more data from FRED
with st.sidebar:
    with st.form('FREDData'):
        new_data = st.text_input("Add FRED Data","FRED CODE")
        name_of_series = st.text_input("Name of data","Enter Name")
        annual = st.checkbox('If monthly data: Calculate percentage annualy?')
        submitted = st.form_submit_button("ADD")
        
        if submitted:
            fred_dict[name_of_series] = [new_data, None, annual]
            with open('saved_series.pkl', 'wb') as f:
                pickle.dump(fred_dict, f)

# Remove data 
with st.sidebar:
    with st.form('Remove Data'):
        data_to_be_removed = st.multiselect('Remove Data From Database', fred_dict.keys())
        submitted = st.form_submit_button("Remove")
        if submitted:
            for item in data_to_be_removed:
                fred_dict.pop(item)
            with open('saved_series.pkl', 'wb') as f:
                pickle.dump(fred_dict, f)


if len(selected_indicators) > 0:
    tab1, tab2 = st.tabs(['Time-Series', 'Percent Change'])
else: 
    tab1 = st.tabs(['Time-Series'])[0]
    tab2 = None


series_objects = []    # store series (Data) objects 


with tab1:
    if len(selected_indicators) > 0:
        chart_type = st.selectbox('Chart Type', ('line', 'area'))
    else:
        st.text_area(label="Get Started", value = "Select a time series on the left", height=30)
        

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

    if not stop:
        for i, ind in enumerate(selected_indicators):
            
                with columns[i%n_cols]:
                    try:
                        series = Data(fred_dict[ind][0], ind, start, fred_dict[ind][1], end, fred_dict[ind][2])
                    except Exception:
                        try:
                            series = Data(fred_dict[ind][0], ind, start, fred_dict[ind][1], end)
                        except Exception:
                            pass

                    series.get_data()
                    series_objects.append(series)
                    series.write_data(chart_type)


selected_indicators_for_pct = selected_indicators.copy()

try:
    selected_indicators_for_pct.remove("10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity")
except ValueError:
    pass

# calculate and display percentage change of selected time series on second tab
if tab2 is not None:
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




