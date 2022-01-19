"""
Script for displaying graphs of SAR parameters and NDVI values from a database in a streamlit web app

Authors: Markus Adam, Laura Walder
Date created: 13/10/2021
Date last modified: 09/01/2022
Python version: 3.8
"""
# import packages
import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# set app page layout
st.set_page_config(layout="wide")

# get path to database from user and check if path is valid
text_input_container = st.empty()
db_path = text_input_container.text_input("Please enter path to database: ")
if db_path != "" and db_path.endswith(".db") is False:
    st.error("Entered path does not contain a database")

# display app contents if database path is valid
elif db_path.endswith(".db"):

    # remove prompt of database path input
    text_input_container.empty()

    # C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db
    # try connection to database (db)
    try:
        db = sqlite3.connect(db_path)
        print("Successfully Connected to SQLite Database")
    except sqlite3.Error as error:
        print("Error while connecting to Database", error)

    # create app title and description
    st.title('Radar Crop Monitor App')
    st.markdown('This app can be used to display SAR parameters and NDVI values for crop monitoring.')
    st.markdown("Please select the main and dependent filter first. Note that displaying the data may take some time.")
    st.markdown('#')

    # create titles for data filters
    st.sidebar.title("Filters")
    st.sidebar.markdown("#")
    st.sidebar.header('Main Filters')

    # load unique values from specific table columns of db to use as selectable values (main and dependent filters)
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

    st.sidebar.markdown('#')
    st.sidebar.header('Dependent Filters')

    # get tuples of multiselections (dependent filters) from user
    acq_selection = tuple(st.sidebar.multiselect("Acquisition Mode", acq_types))
    product_selection = tuple(st.sidebar.multiselect("Product", products))
    param_selection = tuple(st.sidebar.multiselect("Parameter", parameter))
    fid_selection = tuple(st.sidebar.multiselect("FID", fid))

    # print data source and contributors
    st.sidebar.markdown("#")
    st.sidebar.markdown("Data Source: ESA Copernicus-Data")
    st.sidebar.markdown("Contributors: Markus Adam, Laura Walder")

    # list of multiselection tuples
    dependent_selections = [acq_selection, product_selection, param_selection, fid_selection]

    # function to add placeholder to multiselection tuple if len == 1 (prevents syntax error in sql query)


    def placeholders(multiselections):
        if len(multiselections) == 1:
            multiselections = multiselections + ("placeholder",)
            return multiselections
        else:
            return multiselections


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
            st.warning("No selection has been made. Please select filter combinations.")
        else:
            st.error("No data is available for this filter combination. Please select other filter combinations.")

    # define expander box for time slider and trendline selection
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
    selection = alt.selection_multi(fields=['acquisition'], bind='legend')

    # get earliest and latest date again from now date-filtered df
    start_date = records["datetime"].min()
    end_date = records["datetime"].max()

    # set domain containing earliest and latest date in df, used as boundaries for x-axis of charts
    domain_pd = pd.to_datetime([start_date, end_date]).astype(int) / 10 ** 6

    # set y-axis label based on selected statistic
    if stat_selection in ["mean", "median", "std", "mode_value_1"]:
        y_axis_label_db = "Backscatter [dB]"
        y_axis_label_ndvi = "NDVI value"
    else:
        y_axis_label_db = "Value"
        y_axis_label_ndvi = "Value"

    # VV polarization charts
    vv_chart = alt.Chart(vv_records).mark_circle().encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_db, titleFontSize=22)),
        color=alt.condition(selection, "acquisition", alt.value("lightgray"), sort=["D"]),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
        properties(title="VV Polarization", width=1000, height=500)
    vv_loess = alt.Chart(vv_records).encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_db, titleFontSize=22))).transform_filter(selection).\
        transform_loess("datetime", "value").mark_line(color="red")
    vv_mean = alt.Chart(vv_records).mark_line(color="red").transform_filter(selection).\
        transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

    # VH polarization charts
    vh_chart = alt.Chart(vh_records).mark_circle().encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_db, titleFontSize=22)),
        color=alt.condition(selection, "acquisition", alt.value("lightgray"), sort=["D"]),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
        properties(title="VH Polarization", width=1000, height=500)
    vh_loess = alt.Chart(vh_records).encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_db, titleFontSize=22))).transform_filter(selection).\
        transform_loess("datetime", "value").mark_line(color="red")
    vh_mean = alt.Chart(vh_records).mark_line(color="red").transform_filter(selection).\
        transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

    # NDVI charts
    ndvi_chart = alt.Chart(ndvi_records).mark_circle().encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_ndvi, titleFontSize=22)),
        color=alt.condition(selection, "acquisition", alt.value("lightgray"), sort=["D"]),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
        properties(title="NDVI", width=1000, height=500)
    ndvi_loess = alt.Chart(ndvi_records).encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
        y=alt.Y("value", axis=alt.Axis(title=y_axis_label_ndvi, titleFontSize=22))).transform_filter(selection).\
        transform_loess("datetime", "value").mark_line(color="red")
    ndvi_mean = alt.Chart(ndvi_records).mark_line(color="red").transform_filter(selection).\
        transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

    # add trend line type to charts based on user selection
    if stat_button == "LOESS":
        vv_chart = vv_chart + vv_loess
        vh_chart = vh_chart + vh_loess
        ndvi_chart = ndvi_chart + ndvi_loess

    elif stat_button == "Rolling Mean":
        vv_chart = vv_chart + vv_mean
        vh_chart = vh_chart + vh_mean
        ndvi_chart = ndvi_chart + ndvi_mean

    # define list of charts to be displayed, based on user selection and data availability
    chart_list = []
    if records["parameter"].str.contains("VV").any() and "VV" in param_selection:
        chart_list.append(vv_chart)
    if records["parameter"].str.contains("VH").any() and "VH" in param_selection:
        chart_list.append(vh_chart)
    if records["parameter"].str.contains("NDVI").any() and "NDVI" in param_selection:
        chart_list.append(ndvi_chart)

    # display charts from list
    for chart in chart_list:
        st.altair_chart(chart.configure_title(fontSize=28).configure_legend(titleFontSize=20, labelFontSize=18))

    # close connection to db
    db.close()
