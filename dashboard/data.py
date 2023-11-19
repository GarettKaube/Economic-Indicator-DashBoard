import utils
import pandas as pd
from fredapi import Fred
import streamlit as st
import utils
import pickle
import datetime
import plotly.graph_objects as go
import plotly.express as px





# innitialization
with open("apikey.txt", 'r') as f:
    API_KEY  = f.read().strip()
    
fred = Fred(api_key=API_KEY)
series_header_size = 6

class Data:
    def __init__(self, series_code:str, series_name:str, annual_pct = None):
        self.series = series_code
        self.name = series_name
        
        self.start = None
        self.end = None

        self.period = None
        self.percent_chg = None
        self.annual_pct = annual_pct
        
        self.data = None
        
@utils.add_to_class(Data)
def set_start_end_dates(self, start, end, period = None):
    self.start = start
    self.end = end
    self.period = period

@utils.add_to_class(Data)
def get_data(self):
    """
    Downloads FRED data if it is not already downloaded
    returns: None
    """
    try:
        data = pd.read_csv(f"./data/{self.name}.csv",index_col=0)
        
        data.index = pd.to_datetime(data.index)
    except Exception:
        try:
            data = fred.get_series_latest_release(self.series)
            data.to_csv(f"./data/{self.name}.csv")
        except Exception:
            st.write('\"{}\" is not available.'.format(self.name))
    else:
        self.data = utils.add_names(data, self.name[:17])
        if self.period == None:
            self.infer_freq()
        self.last_vals = self.data.tail(4)
        

    
@utils.add_to_class(Data)
def plot_data(self, chart_type = 'line'):
        """
        Lets user use the date slider to select date end points then plots the time series. Can plot line or area charts.
        chart_type: 'line' or 'area'
        """
        if self.data is not None:
            fig = go.Figure()

            date_interval = st.slider("Date range", 
                                      value=(datetime.date(self.start.year, self.start.month, self.start.day), datetime.date(self.end.year, self.end.month, self.end.day)),
                                      key=self.name)
            
            self.start = pd.Timestamp(date_interval[0].year, date_interval[0].month, date_interval[0].day)
            self.end = pd.Timestamp(date_interval[1].year, date_interval[1].month, date_interval[1].day)

            st.write("""
                    {} {}
                     """.format('#'*series_header_size, self.name)
                    )
            
            data_filtered = self.data[(self.data.index >= self.start) & (self.data.index <= self.end)]
            data_filtered_df = data_filtered.reset_index()
            
            if chart_type =='line':
                fig.add_trace(go.Scatter(
                    x=data_filtered_df['Date'],
                    y = data_filtered_df[data_filtered_df.columns[1]]
                ))
            
            elif chart_type == 'area':
                fig = px.area(data_filtered_df.ffill(), x='Date', y=data_filtered_df.columns[1])

            st.plotly_chart(fig, use_container_width=True)

            

@utils.add_to_class(Data)
def write_latest_vals(self,n=4):
        if self.data is not None:
            latest = self.data.tail(n)
            st.write("""
            ##### LATEST {}
                """.format(self.name[:17]+"..."))
            st.write(latest)


@utils.add_to_class(Data)
def get_series(self):
     return self.data



@utils.add_to_class(Data)
def plot_pct_chg(self):
     if self.data is not None:
        period = self.period * 12 if self.annual_pct == True else self.period

        self.percent_chg = ((self.data.diff(period)/ self.data.abs().shift(period))*100).dropna()
        
        percent_chg_filtered = self.percent_chg[(self.percent_chg.index <= self.end) & (self.percent_chg.index >= self.start)]
        st.write("""
            {} Percent Change for {}
        """.format('#'*series_header_size, self.name))
        if percent_chg_filtered.size > 1:
        
            st.line_chart(percent_chg_filtered)
        else:
            st.write("""### Not enough data to calculate percent change""")



# Dictionary that is of the form: "Series name": ["Fred Code", Period]
with open('saved_series.pkl', 'rb') as f:
    fred_dict = pickle.load(f)
    

@utils.add_to_class(Data)
def infer_freq(self):
     if self.data is not None:
        freq = pd.infer_freq(self.data.index)
        if freq == "QS-OCT":
            self.period = 4
        else:
            self.period = 1