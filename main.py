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
products = pd.read_sql_query("select distinct product from s1fieldstatistic;", db)
units = pd.read_sql_query("select distinct unit from s1fieldstatistic;", db)
acq_types = pd.read_sql_query("select distinct acquisition from s1fieldstatistic;", db)
polarization = pd.read_sql_query("select distinct polarization from s1fieldstatistic;", db)
stats = pd.read_sql_query("select distinct statistic from s1fieldstatistic;", db)
fid = pd.read_sql_query("select distinct fid from areaofinterest;", db)

# get single value selections from user
aoi_selection = st.sidebar.selectbox("Select AOI", aoi_names)
year_selection = st.sidebar.selectbox("Select Year", years)
product_selection = st.sidebar.selectbox("Select Product Level", products)
unit_selection = st.sidebar.selectbox("Select Unit", units)
stat_selection = st.sidebar.selectbox("Select Statistic", stats)

st.sidebar.markdown('#')
st.sidebar.header('Dependent Filters')

# get list of multiselections from user
acq_selection = tuple(st.sidebar.multiselect("Select Acquisition Mode", acq_types))
pol_selection = tuple(st.sidebar.multiselect("Select Polarization", polarization))
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
fid_selection = placeholders(fid_selection)

CROP_TYPE_CODE = 'WW'
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
    area.crop_type_code = "{CROP_TYPE_CODE}"
    AND s1.aoi="{aoi_selection}"
    AND area.year="{year_selection}"
    AND s1.product="{product_selection}"
    AND s1.acquisition IN {repr(acq_selection)}
    AND s1.polarization IN {repr(pol_selection)}
    AND s1.unit="{unit_selection}"
    AND area.fid IN {repr(fid_selection)}
    AND s1.statistic = "{stat_selection}"
    ORDER BY s1.mask_label, s1.datetime  ASC; """

records = pd.read_sql(sql, db)

st.dataframe(records)

# chart
selection = alt.selection_multi(fields=['acquisition'], bind='legend')
chart = alt.Chart(records).mark_circle().encode(
    x="datetime", y="value", color=alt.condition(
        selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection)
st.altair_chart(chart, use_container_width=True)

cursor.close()
db.close()
