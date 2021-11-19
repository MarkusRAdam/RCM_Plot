import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# connection to db
try:
    db = sqlite3.connect(
        'C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db')
    cursor = db.cursor()
    print("Successfully Connected to SQLite Database")
except sqlite3.Error as error:
    print("Error while connecting to Database", error)

# create sider
st.sidebar.title('Radar Crop Monitor APP')
st.sidebar.markdown('_Short Description of the Project & Contributors ... _')
st.sidebar.markdown('#')
st.sidebar.markdown('#')
st.sidebar.header('Main Filters')

# load values from specific table columns for value selection by user
aoi_names = pd.read_sql_query('select distinct aoi from areaofinterest;', db)
years = pd.read_sql_query("select distinct year from areaofinterest;", db)
crop_types = pd.read_sql_query("select distinct crop_type from croplegend;", db)
products = pd.read_sql_query("select distinct product from s1fieldstatistic;", db)
#units = pd.read_sql_query("select distinct unit from s1fieldstatistic;", db)
acq_types = pd.read_sql_query("select distinct acquisition from s1fieldstatistic;", db)
polarization = pd.read_sql_query("select distinct polarization from s1fieldstatistic;", db)
stats = pd.read_sql_query("select distinct statistic from s1fieldstatistic;", db)
fid = pd.read_sql_query("select distinct fid from areaofinterest;", db)

# get single value selections from user
aoi_selection = st.sidebar.selectbox("Select AOI", aoi_names)
year_selection = st.sidebar.selectbox("Select Year", years)
crop_selection = st.sidebar.selectbox("Select Crop Type", crop_types)
#product_selection = st.sidebar.selectbox("Select Product Level", products)
#unit_selection = st.sidebar.selectbox("Select Unit", units)
stat_selection = st.sidebar.selectbox("Select Statistic", stats)

st.sidebar.markdown('#')
st.sidebar.header('Dependent Filters')

# get list of multiselections from user
acq_selection = tuple(st.sidebar.multiselect("Select Acquisition Mode", acq_types))
pol_selection = tuple(st.sidebar.multiselect("Select Polarization", polarization))
product_selection = tuple(st.sidebar.multiselect("Select Product", products))
fid_selection = tuple(st.sidebar.multiselect("Select FID", fid))


# function to add placeholder to multiselection tuple if len == 1 (prevents syntax error)
def placeholders(multiselections):
    if len(multiselections) == 1:
        multiselections = multiselections + ("placeholder",)
        return multiselections
    else:
        return multiselections


# apply placeholder function
acq_selection = placeholders(acq_selection)
pol_selection = placeholders(pol_selection)
product_selection = placeholders(product_selection)
fid_selection = placeholders(fid_selection)

# CROP_TYPE_CODE = 'WW'
# AOI = 'FRIEN'
# YEAR = '2017'
# PRODUCT = 'GRD'
# ACQ = 'A'
# POLARIS = 'VV'
# UNIT = 'dB'
# FID = '36'
# STATISTIC = 'median'

# define sql body
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
    AND s1.polarization IN {repr(pol_selection)}
    AND area.fid IN {repr(fid_selection)}
    AND s1.statistic = "{stat_selection}"
    ORDER BY s1.mask_label, s1.datetime  ASC; """

records = pd.read_sql(sql, db)

# create sliders for time frame selection (start and end date of time series plots)
# convert datetime string column to datetime
records["datetime"] = pd.to_datetime(records["datetime"])
records["datetime"] = pd.to_datetime(records['datetime']).apply(lambda x: x.date())

# get earliest and latest date from dataset as boundaries for slider
start_date = records["datetime"].min()
end_date = records["datetime"].max()

# define slider values from user selection
slider_1, slider_2 = st.slider('Select date range', value=(start_date, end_date), format="MM/DD/YY - hh:mm:ss")

# filter dataframe based on slider values
records = records[(records['datetime'] > slider_1) & (records['datetime'] < slider_2)]

st.dataframe(records)

# filter records by polarisation/value for different plots
vv_records = records[records["parameter"] == "VV"]
vh_records = records[records["parameter"] == "VH"]
ndvi_records = records[records["parameter"] == "NDVI"]

# set columns for values to be colored by
selection = alt.selection_multi(fields=['acquisition'], bind='legend')

# VV polarization chart
vv_chart = alt.Chart(vv_records).mark_circle().encode(
    x=alt.X("datetime", axis=alt.Axis(title='Date')),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter')),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="VV Polarization")
#st.altair_chart(vv_chart, use_container_width=True)

# VH polarization chart
vh_chart = alt.Chart(vh_records).mark_circle().encode(
    x=alt.X("datetime", axis=alt.Axis(title='Date')),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter')),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="VH Polarization")
#st.altair_chart(vh_chart, use_container_width=True)

# NDVI chart
ndvi_chart = alt.Chart(ndvi_records).mark_circle().encode(
    x=alt.X("datetime", axis=alt.Axis(title='Date')),
    y=alt.Y("value", axis=alt.Axis(title='NDVI Value')),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="NDVI")
#st.altair_chart(ndvi_chart, use_container_width=True)

st.altair_chart(alt.vconcat(vv_chart, vh_chart, ndvi_chart))
cursor.close()
db.close()
