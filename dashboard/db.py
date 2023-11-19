
import numpy as np
import pandas as pd
from fredapi import Fred
import streamlit as st
import utils
import pickle
import datetime
import plotly.graph_objects as go
import plotly.express as px
import time
import os



st.set_page_config(layout="wide")

# innitialization
with open("apikey.txt", 'r') as f:
    API_KEY  = f.read().strip()
    
fred = Fred(api_key=API_KEY)
series_header_size = 6
gap = "medium"

with open('saved_series.pkl', 'rb') as f:
    fred_dict = pickle.load(f)



class SideBar:
    def __init__(self) -> None:
        st.sidebar.header('Economic Indicator Selection')
        self.selected_indicators = st.sidebar.multiselect('Indicator', fred_dict.keys()) #selection area to select time-series
        self.num_indicators = len(self.selected_indicators)
        self.stop = None
        self.start = None
        self.end = None

    def __select_data(self):
        with st.sidebar:
            start_select = st.date_input('Start of Time Series', value =datetime.date(2014,1,1), min_value=datetime.date(1960,1,1))
            # update global time series start
            self.start = pd.Timestamp(start_select.year, start_select.month, start_select.day) 

            end_select = st.date_input('End of Time Series', min_value=datetime.date(1960,1,1))
            
            # update global time series end
            self.end = pd.Timestamp(end_select.year, end_select.month, end_select.day) 

            # make sure the start date is before the end date
            try:
                assert self.end >= self.start
            except AssertionError:
                st.markdown(":red[Start should be before end date!]")
                self.stop = True # stop the dashboard if we have an error
            else:
                self.stop = False
        

    def __get_more_data(self):
        # Get more data from FRED
        with st.sidebar:
            with st.form('FREDData'):
                new_data_code = st.text_input("Add FRED Data","FRED CODE")
                new_data_name = st.text_input("Name of data","Enter Name")
                if_annual_pct = st.checkbox('If monthly data: Calculate percentage annualy?')
                submitted = st.form_submit_button("ADD")

                if submitted:
                    self.__check_data_submission(self, new_data_code, new_data_name, if_annual_pct)


    def __check_data_submission(self, new_data_code, new_data_name, if_annual_pct):
        """ Checks for valid FRED time series codes and valid names then adds the information onto fred dict in the form if both are valid:
        fred_dict[new_data_name] = [FRED_CODE:str, Period:int, if_annual_pct:bool]
        """
        check_for_invalid_FRED_Code = new_data_code.replace(" ", "") == "" or new_data_code == "FRED CODE"
        check_for_invalid_name = new_data_name.replace(" ", "") == "" or new_data_name == "Enter Name"
        if check_for_invalid_FRED_Code:
            st.markdown(":red[Enter the FRED code for the Time Series!]")

            if check_for_invalid_name:
                st.markdown(":red[Enter a name for the Time Series!]")

        elif check_for_invalid_name and not check_for_invalid_FRED_Code:
            st.markdown(":red[Enter a name for the Time Series!]")

        # Valid name and code
        else:
            # New_data is the FRED code, if_annual_pct is bool to check if we calculate percentage change on an annual basis
            fred_dict[new_data_name] = [new_data_code, None, if_annual_pct] 
            with open("saved_series.pkl", 'wb') as f:
                pickle.dump(fred_dict, f)   

    
    def __remove_data(self):
        """Removes entries from the fred_dict dictionary given input from the sidebar
        """
        with st.sidebar:
            with st.form("Remove Data"):
                data_to_be_removed = st.multiselect("Remove Data From Database", fred_dict.keys())
                submitted = st.form_submit_button("Remove")
                if submitted:
                    for item in data_to_be_removed:
                        fred_dict.pop(item)
                    with open("saved_series.pkl", 'wb') as f:
                        pickle.dump(fred_dict, f)


    def place_sidebar(self):
        self.__select_data()
        self.__get_more_data()
        self.__remove_data()


class Dashboard:
    def __init__(self, tab = None) -> None:
        self.series_objects = []    # store series (Data) objects 
        self.sidebar = SideBar()
        self.sidebar.place_sidebar()
        self.time_series_tab, self.pct_tab, self.data_tab, self.summary_tab = utils.get_tabs(self.sidebar.num_indicators)


    def place_tabs(self):
        # Time-series tab
        if self.time_series_tab is not None:
            self.__place_timeseries_tab()

        # other tabs
        self.__place_percent_change_tab(self.pct_tab)
        self.__place_data_tab(self.data_tab)


    def __place_timeseries_tab(self):
        with self.time_series_tab:
            # add select chart drop down menu when there is at least one time series selected
            chart_type = st.selectbox("Chart Type", ('line', 'area'))

            # set number of columns depending on how many time-series are selected
            if self.sidebar.num_indicators >= 2:
                columns = st.columns(2, gap = gap)
                num_columns = 2
            else:
                columns = st.columns(1, gap = gap)
                num_columns = 1

            # make series objects and display time plots of selected series
            if not self.sidebar.stop:
                self.__make_data_objects()
                self.__place_plots(columns, num_columns, chart_type)


    def __make_data_objects(self):
        """
        Gets data and plots. Creates more streamlit columns as more time-series is added
        """
        from data import Data

        for i, indicator_name in enumerate(self.sidebar.selected_indicators):
            
            FRED_time_series = fred_dict[indicator_name]
            FRED_time_series_code = FRED_time_series[0]
            FRED_time_series_period = FRED_time_series[1]

            try:
                FRED_time_series_pct_freq = FRED_time_series[2]
                series = Data(FRED_time_series_code, indicator_name, FRED_time_series_pct_freq)
                
            # When there is no annual_pct in fred_dict
            except IndexError:
                series = Data(FRED_time_series_code, indicator_name)
                
            finally:
                # Change start and ending dates to match sidebar settings
                series.set_start_end_dates(self.sidebar.start, self.sidebar.end, FRED_time_series_period)
                series.get_data()
                self.series_objects.append(series)
                #series.write_data(charttype)


    def __place_plots(self, columns, num_cols, chart_type):
        for i, series in enumerate(self.series_objects):
            with columns[i % num_cols]:
                series.plot_data(chart_type)


    def __place_percent_change_tab(self, tab):
        """
        Plots the percent change of the selected time-series.
        """
        if tab is not None:
            with tab:

                if self.sidebar.num_indicators >= 2:
                    columns_pct = st.columns(2, gap = gap)
                    n_cols_pct = 2
                else:
                    columns_pct = st.columns(1, gap = gap)
                    n_cols_pct = 1

                for i, series in enumerate(self.series_objects):
                    with columns_pct[i%n_cols_pct]:
                        if series.name in self.sidebar.selected_indicators:
                            series.plot_pct_chg()


    def __place_data_tab(self, tab):
        if tab is not None:
            with tab:
                max = st.number_input("Maximum amount of latest values to display:", min_value=1, max_value=20, value=4)
                columns = st.columns(5, gap='medium')
                for i in range(1,6):
                    if self.sidebar.num_indicators == i:
                        columns = st.columns(i, gap='medium')   

                for i, series in enumerate(self.series_objects):
                    with columns[i%5]:
                        series.write_latest_vals(max)


def main():
    os.makedirs("./data", exist_ok=True)
    time_series = Dashboard()
    time_series.place_tabs()
    

if __name__ == "__main__":
    main()
