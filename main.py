"""
Script for displaying graphs of SAR parameters and NDVI values from a database in a streamlit web app.

Authors: Markus Adam, Laura Walder
Date created: 13/10/2021
Date last modified: 02/02/2022
Python version: 3.8
"""
# import packages
import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db
# set app page layout
st.set_page_config(layout="wide")

# !!! permanent database path can be defined here to avoid path query within the app on every app start !!!
# !!! if you want to keep the app query functionality (default), please do not change the path variable !!!
permanent_db_path = "Enter path here"


# define function for establishing connection to database
def db_connect(db_path):
    """
    Tries connecting to database & gets dataframe of all table names (which will be empty if database path is invalid),
    prints error if connection is unsuccessful.

    :param db_path: path to database file
    :return: connection to database, dataframe with table names
    """
    try:
        database = sqlite3.connect(db_path)
        table_names = pd.read_sql_query("SELECT * FROM sqlite_master WHERE type='table'", database)
        return database, table_names
    except sqlite3.Error as error:
        connection_error = "Error while connecting to database:" + str(error)
        st.error(connection_error)


# define function to get path to database from user and check if path is valid
def db_path_query(permanent_db_path):
    """
    First checks if permanent database path has been set. If yes, it checks if this path is valid and tries
    connecting to database. If no, it queries path from user in the app and tries connection with entered path.
    Path validity is checked by checking path ending (must be ".db") and table_names (which is empty if path is invalid)

    :param permanent_db_path: permanent database path that can be set by user in this script. Default: "Enter path here"
    :return: connection to database
    """
    if permanent_db_path == "Enter path here":
        text_input_container = st.empty()
        path = text_input_container.text_input("Please enter path to database: ")
        if path != "" and path.endswith(".db") is False:
            st.error("Entered path does not contain a valid database")
        elif path.endswith(".db"):
            database, table_names = db_connect(path)
            if table_names.empty:
                st.error("Entered path does not contain a valid database")
            else:
                text_input_container.empty()
                return database
    else:
        if permanent_db_path.endswith(".db"):
            database, table_names = db_connect(permanent_db_path)
            if table_names.empty:
                st.error("Permanent database path does not contain a valid database")
            else:
                return database
        else:
            st.error("Permanent database path does not contain a valid database")


# function to add placeholder to multiselection tuple if len == 1 (prevents syntax error in sql query)
def placeholders(multiselections):
    """
    Adds placeholder string to tuples if their length is 1. This prevents a syntax error in the sql query

    :param multiselections: tuple with user-selected multiselection filter values
    :return: tuple with filter values and optional placeholder
    """
    if len(multiselections) == 1:
        multiselections = multiselections + ("placeholder",)
        return multiselections
    else:
        return multiselections


# define function to make charts
def make_charts(pol_records, axis_label, domain, selection, title, stat_button):
    """
    Creates charts from subset of dataframe records and combines them into one

    :param pol_records: subset of records with one polarisation/value (VV,VH,NDVI)
    :param axis_label: string with y-axis label
    :param domain: boundaries for x-axis (start and end date)
    :param selection: dataframe column by which data points are colored
    :param title: string with chart title
    :param stat_button: name of trendline selected by user
    :return: chart with either VV/VH/NDVI values (and trend line if selected)
    """
    value_chart = alt.Chart(pol_records).mark_circle().encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22),
                scale=alt.Scale(domain=list(domain))),
        y=alt.Y("value", axis=alt.Axis(title=axis_label, titleFontSize=22)),
        color=alt.condition(selection, "acquisition", alt.value("lightgray"), sort=["D"]),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection). \
        properties(title=title, width=1000, height=500)
    loess_chart = alt.Chart(pol_records).encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22),
                scale=alt.Scale(domain=list(domain))),
        y=alt.Y("value", axis=alt.Axis(title=axis_label, titleFontSize=22))).transform_filter(selection). \
        transform_loess("datetime", "value").mark_line(color="red")
    mean_chart = alt.Chart(pol_records).mark_line(color="red").transform_filter(selection). \
        transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

    if stat_button == "LOESS":
        final_chart = value_chart + loess_chart
    elif stat_button == "Rolling Mean":
        final_chart = value_chart + mean_chart
    else:
        final_chart = value_chart

    return final_chart


# define function to fill list of charts that will be displayed
def collect_charts(vv_vh_ndvi, vv_vh_ndvi_chart, param_selection, records, chart_list):
    """
    Fills list with chart if the corresponding parameter was selected and is available,
    returns warning if not.

    :param vv_vh_ndvi: parameter (VV,VH,NDVI)
    :param vv_vh_ndvi_chart: chart made with make_charts() function
    :param param_selection: parameters (VV/VH/NDVI) selected by user
    :param records: dataframe with data that will be displayed
    :param chart_list: list o charts to be displayed
    :return: warning if no data is available for selected parameter
    """
    if vv_vh_ndvi in param_selection:
        if records["parameter"].str.contains(vv_vh_ndvi).any():
            chart_list.append(vv_vh_ndvi_chart)
        elif records.empty is False:
            param_warning = "No data available for parameter {}".format(vv_vh_ndvi)
            return st.warning(param_warning)


# define function for deploying main page of app
def main_part(db):
    """
    Deploys the main page of the app and its functionalities. This includes defining the data filters,
    querying the filtered data from the database, and displaying charts of the data in the app.

    :param db: connection to database
    :return: streamlit app functionalities (filters, charts)
    """
    # print app title and description
    st.title('Radar Crop Monitor App')
    st.markdown('This app can be used to display SAR parameters and NDVI values for crop monitoring.')
    st.markdown("Please select the main and dependent filter first. Note that displaying the data may take some time.")
    st.markdown('#')

    # print titles for data filters in app
    st.sidebar.title("Filter")
    st.sidebar.markdown("#")
    st.sidebar.header('Main Filter')

    # load unique values from specific table columns of db to use as selectable values for main and dependent filters
    aoi_names = pd.read_sql_query('select distinct aoi from areaofinterest;', db)
    years = pd.read_sql_query("select distinct year from areaofinterest;", db)
    crop_types = pd.read_sql_query("select distinct crop_type from croplegend;", db)
    products = pd.read_sql_query("select distinct product from s1fieldstatistic;", db)
    acq_types = pd.read_sql_query("select distinct acquisition from s1fieldstatistic;", db)
    parameter = pd.read_sql_query("select distinct polarization from s1fieldstatistic;", db)
    stats = pd.read_sql_query("select distinct statistic from s1fieldstatistic;", db)
    fid = pd.read_sql_query("select distinct fid from areaofinterest;", db)

    # get single value selections of main filters from user
    aoi_selection = st.sidebar.selectbox("AOI", aoi_names)
    year_selection = st.sidebar.selectbox("Year", years)
    crop_selection = st.sidebar.selectbox("Crop Type", crop_types)
    stat_selection = st.sidebar.selectbox("Statistic", stats)

    # print title for dependent filters in app
    st.sidebar.markdown('#')
    st.sidebar.header('Dependent Filter')

    # get tuples of multiselections (dependent filters) from user
    acq_selection = tuple(st.sidebar.multiselect("Acquisition Mode", acq_types))
    product_selection = tuple(st.sidebar.multiselect("Product", products))
    param_selection = tuple(st.sidebar.multiselect("Parameter", parameter))
    fid_selection = tuple(st.sidebar.multiselect("FID", fid))

    # print data source and contributors in app
    st.sidebar.markdown("#")
    st.sidebar.markdown("Data Source: ESA Copernicus-Data")
    st.sidebar.markdown("Contributors: Markus Adam, Laura Walder")

    # define list of multiselection tuples
    dependent_selections = [acq_selection, product_selection, param_selection, fid_selection]

    # apply placeholder function to multiselection tuples
    acq_selection = placeholders(acq_selection)
    param_selection = placeholders(param_selection)
    product_selection = placeholders(product_selection)
    fid_selection = placeholders(fid_selection)

    # define sql body for query, with filter selections as variables
    sql = f"""SELECT 
        round(s1.value, 2) as value, 
        s1.mask_label, 
        s1.unit, 
        s1.aoi, 
        s1.datetime, 
        strftime('%Y-%m-%d', s1.datetime) as date,
        strftime('%H:%M:%S', s1.datetime) as time,
        s1.polarization as parameter, 
        s1.acquisition, 
        s1.product,
        area.fid, 
        area.year, 
        area.sl_nr, 
        area.crop_type_code, 
        area.crop_type,
        area.field_geom
        FROM s1fieldstatistic as s1
        INNER JOIN (SELECT 
        areaofinterest.fid, 
        areaofinterest.year, 
        areaofinterest.aoi,
        areaofinterest.sl_nr, 
        areaofinterest.crop_type_code, 
        crop.crop_type,
        areaofinterest.field_geom
        FROM areaofinterest
        INNER JOIN croplegend as crop 
        ON (crop.crop_type_code = areaofinterest.crop_type_code)) area
        ON (s1.mask_label = area.fid AND strftime('%Y', s1.datetime)=area.year AND s1.aoi = area.aoi)
        WHERE 
        s1.aoi="{aoi_selection}"
        AND area.crop_type="{crop_selection}"
        AND area.year="{year_selection}"
        AND s1.product IN {repr(product_selection)}
        AND s1.acquisition IN {repr(acq_selection)}
        AND s1.polarization IN {repr(param_selection)}
        AND area.fid IN {repr(fid_selection)}
        AND s1.statistic = "{stat_selection}"
        ORDER BY s1.mask_label, s1.datetime  ASC; """

    # apply sql query and load resulting table as dataframe
    records = pd.read_sql(sql, db)

    # print warning when no filter is selected and error when invalid filter combination (with no data) is selected
    if records.empty:
        if any(len(x) == 0 for x in dependent_selections):
            st.warning("No selection has been made. Please select filter combination.")
        else:
            st.error("No data is available for this filter combination. Please select other filter combinations.")

    # define expander box which will contain time slider and trendline selection functionalities
    expander = st.expander("Date Range and Trendline Filter", expanded=True)

    # create sliders for date range selection (start and end date of x-axis of charts)

    # convert datetime string column to datetime
    records["datetime"] = pd.to_datetime(records['datetime']).apply(lambda x: x.date())

    # get earliest and latest date from df as boundaries for slider
    start_date = records["datetime"].min()
    end_date = records["datetime"].max()

    # define slider values from user selection and filter df based on these values
    try:
        expander.subheader("Select date range")
        slider_1, slider_2 = expander.slider('', value=(start_date, end_date), format="DD.MM.YY")
        records = records[(records['datetime'] >= slider_1) & (records['datetime'] <= slider_2)]
    except KeyError:
        expander.warning("Date range slider is only available after a valid filter combination has been selected")

    # make button for selection of trend line type
    expander.markdown("#")
    expander.subheader("Select trendline")
    stat_button = expander.radio("", ("None", "LOESS", "Rolling Mean"))
    st.markdown("#")

    # create charts (scatterplots and trendlines (LOESS/Rolling mean)) for VV, VH and NDVI values

    # get subsets of df by filtering by polarisation/value for different charts
    vv_records = records[records["parameter"] == "VV"]
    vh_records = records[records["parameter"] == "VH"]
    ndvi_records = records[records["parameter"] == "NDVI"]

    # set df column by which points are colored in charts
    color_selection = alt.selection_multi(fields=['acquisition'], bind='legend')

    # get earliest and latest date again from now date-filtered df
    start_date = records["datetime"].min()
    end_date = records["datetime"].max()

    # set domain containing earliest and latest date in df, used as boundaries for x-axis of charts
    domain_pd = pd.to_datetime([start_date, end_date]).view("int64") / 10 ** 6

    # set y-axis label based on user-selected statistic
    if stat_selection in ["mean", "median", "std", "mode_value_1"]:
        y_axis_label_db = "Backscatter [dB]"
        y_axis_label_ndvi = "NDVI value"
    else:
        y_axis_label_db = "Value"
        y_axis_label_ndvi = "Value"

    # set chart titles
    vv_title = "VV Polarisation"
    vh_title = "VH Polarisation"
    ndvi_title = "NDVI"

    # apply function to make charts
    vv_chart = make_charts(vv_records, y_axis_label_db, domain_pd, color_selection, vv_title, stat_button)
    vh_chart = make_charts(vh_records, y_axis_label_db, domain_pd, color_selection, vh_title, stat_button)
    ndvi_chart = make_charts(ndvi_records, y_axis_label_ndvi, domain_pd, color_selection, ndvi_title, stat_button)

    # define list that will be filled with charts to be displayed
    chart_list = []

    # apply function to fill chart list
    collect_charts("VV", vv_chart, param_selection, records, chart_list)
    collect_charts("VH", vh_chart, param_selection, records, chart_list)
    collect_charts("NDVI", ndvi_chart, param_selection, records, chart_list)

    # display charts from list
    for chart in chart_list:
        st.altair_chart(chart.configure_title(fontSize=28).configure_legend(titleFontSize=20, labelFontSize=18))

    # close connection to db
    db.close()


# establish connection to database
db = db_path_query(permanent_db_path)

# deploy main part of the app if connection to database is established
if db:
    main_part(db)
