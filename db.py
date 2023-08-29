
import numpy as np
import pandas as pd
from fredapi import Fred
import streamlit as st
from utils import *
import pickle
import datetime
import plotly.graph_objects as go
import plotly.express as px
import time
import os


st.set_page_config(layout="wide")

# innitialization
API_KEY = '9a048a276f1a939a1e64c77f214e5684' # MUST BE ADDED. Obtained from FRED 
fred = Fred(api_key=API_KEY)
series_header_size = 6

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
        


@add_to_class(Data)
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
        self.data = add_names(data, self.name[:17])
        if self.period == None:
            self.infer_freq()
        self.last_vals = self.data.tail(4)
        

    
@add_to_class(Data)
def write_data(self, chart_type = 'line'):
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

            

@add_to_class(Data)
def write_latest_vals(self,n=4):
        if self.data is not None:
            latest = self.data.tail(n)
            st.write("""
            ##### LATEST {}
                """.format(self.name[:17]+"..."))
            st.write(latest)


@add_to_class(Data)
def get_series(self):
     return self.data



@add_to_class(Data)
def calculate_pct_chg(self):
     if self.data is not None:
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



# Dictionary that is of the form: "Series name": ["Fred Code", Period]
with open('saved_series.pkl', 'rb') as f:
    fred_dict = pickle.load(f)
    

@add_to_class(Data)
def infer_freq(self):
     if self.data is not None:
        freq = pd.infer_freq(self.data.index)
        if freq == "QS-OCT":
            self.period = 4
        else:
            self.period = 1


class SideBar:
    def __init__(self) -> None:
        st.sidebar.header('Economic Indicator Selection')
        self.selected_indicators = st.sidebar.multiselect('Indicator', fred_dict.keys())
        self.num_indicators = len(self.selected_indicators)
        self.start = None
        self.end = None
        self.stop = None
    def select_data(self):
        with st.sidebar:
            start_select = st.date_input('Start of Time Series', value =datetime.date(2014,1,1), min_value=datetime.date(1960,1,1))
            self.start = pd.Timestamp(start_select.year, start_select.month, start_select.day)

            end_select = st.date_input('End of Time Series', min_value=datetime.date(1960,1,1))
            self.end = pd.Timestamp(end_select.year, end_select.month, end_select.day)

            # make sure the start date is before the end date
            try:
                assert self.end >= self.start
            except AssertionError:
                st.markdown(":red[Start should be before end date!]")
                self.stop = True
            else:
                self.stop = False
        
    def get_more_data(self):
        # Get more data from FRED
        with st.sidebar:
            with st.form('FREDData'):
                new_data = st.text_input("Add FRED Data","FRED CODE")
                name_of_series = st.text_input("Name of data","Enter Name")
                annual = st.checkbox('If monthly data: Calculate percentage annualy?')
                submitted = st.form_submit_button("ADD")

                if submitted:
                    check_for_FRED_Code = new_data.replace(" ", "") == "" or new_data == "FRED CODE"
                    check_for_name = name_of_series.replace(" ", "") == "" or name_of_series == "Enter Name"

                    if check_for_FRED_Code:
                        st.markdown(":red[Enter the FRED code for the Time Series!]")

                        if check_for_name:
                            st.markdown(":red[Enter a name for the Time Series!]")

                    elif check_for_name and not check_for_FRED_Code :
                        st.markdown(":red[Enter a name for the Time Series!]")

                    else:
                        fred_dict[name_of_series] = [new_data, None, annual]
                        with open('saved_series.pkl', 'wb') as f:
                            pickle.dump(fred_dict, f)    

    def remove_data(self):
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



class TimeSeriesTab(SideBar):
    def __init__(self, tab = None) -> None:
        self.series_objects = []    # store series (Data) objects 
        self.tab = tab
        super(TimeSeriesTab, self).__init__()

    def runtab(self):
        # Time-series tab
        if self.tab is not None:
            with self.tab:
                # add select chart drop down menu when there is at least one time series selected
                charttype = st.selectbox('Chart Type', ('line', 'area'))

                # set number of columns depending on how many time-series are selected
                if self.num_indicators >= 2:
                    columns = st.columns(2, gap = 'medium')
                    ncols = 2
                else:
                    columns = st.columns(1, gap = 'medium')
                    ncols = 1

                # make series objects and display time plots of selected series

                if not self.stop:
                    self.make_plots(columns, ncols, charttype)


    def make_plots(self, columns, ncols, charttype):
        """
        Gets data and plots. Creates more streamlit columns as more time-series is added
        """
        for i, ind in enumerate(self.selected_indicators):
            with columns[i%ncols]:
                try:
                    series = Data(fred_dict[ind][0], ind, self.start, fred_dict[ind][1], self.end, fred_dict[ind][2])
                    
                except Exception:
                    try:
                        series = Data(fred_dict[ind][0], ind, self.start, fred_dict[ind][1], self.end)
                    except Exception:
                        pass
                series.get_data()
                self.series_objects.append(series)
                series.write_data(charttype)



def percent_change_tab(selected_indicators, num_indicators, series_objects, tab=None):
    """
    Plots the percent change of the selected time-series.
    """
    if tab is not None:
        with tab:

            if num_indicators >= 2:
                columns_pct = st.columns(2, gap = 'medium')
                n_cols_pct = 2
            else:
                columns_pct = st.columns(1, gap = 'medium')
                n_cols_pct = 1

            for i,s in enumerate(series_objects):
                with columns_pct[i%n_cols_pct]:
                    if s.name in selected_indicators:
                        s.calculate_pct_chg()


def data_tab(tab, num_indicators, series_objects):
    if tab is not None:
        with tab:
            max = st.number_input("Maximum amount of latest values to display:", min_value=1, max_value=20, value=4)
            columns = st.columns(5, gap='medium')
            for i in range(1,6):
                if num_indicators == i:
                    columns = st.columns(i, gap='medium')   

            for i,s in enumerate(series_objects):
                with columns[i%5]:
                    s.write_latest_vals(max)


def main():
    os.makedirs("./data", exist_ok=True)
    
    time_series = TimeSeriesTab()
    time_series.select_data()
    time_series.get_more_data()
    time_series.remove_data()

    time_series_tab, pct_tab, data_tab, summary_tab = get_tabs(time_series.num_indicators)
    time_series.tab = time_series_tab
    
    time_series.runtab()
    percent_change_tab(time_series.selected_indicators, time_series.num_indicators, time_series.series_objects, pct_tab)
    

if __name__ == "__main__":
    main()
