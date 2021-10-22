import streamlit as st
import pandas as pd
import sqlalchemy
import sqlite3
import altair

# connection to db
try:
    db = sqlite3.connect('C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db')
    cursor = db.cursor()
    print("Database created and Successfully Connected to SQLite")
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)

# create sider
st.sidebar.title('Radar Crop Monitor APP')
st.sidebar.markdown('_Short Description of the Project & Contributors ... _')
st.sidebar.markdown('#')
st.sidebar.markdown('#')
st.sidebar.header('Main Filters')

# load values from specific table columns for value selection by user
aoi_names = pd.read_sql_query('select aoi from areaofinterest;', db)
aoi_names = aoi_names["aoi"].drop_duplicates()
years = pd.read_sql_query("select year from areaofinterest;", db)
years = years["year"].drop_duplicates()
products = pd.read_sql_query("select product from s1fieldstatistic;", db)
products = products["product"].drop_duplicates()
units = pd.read_sql_query("select unit from s1fieldstatistic;", db)
units = units["unit"].drop_duplicates()

# get single value selections from user
aoi_selection = st.sidebar.selectbox("Select AOI", aoi_names)
year_selection = st.sidebar.selectbox("Select Year", years)
product_selection = st.sidebar.selectbox("Select Product", products)
unit_selection = st.sidebar.selectbox("Select Unit", units)

CROP_TYPE_CODE = 'WW'
#AOI = 'FRIEN'
#YEAR = '2017'
#PRODUCT = 'GRD'
ACQ = 'A'
POLARIS = 'VV'
#UNIT = 'dB'
FID = '36'
STATISTIC = 'median'

## define sql body
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
    AND s1.acquisition="{ACQ}"
    AND s1.polarization="{POLARIS}"
    AND s1.unit="{unit_selection}"
    AND area.fid="{FID}"
    AND s1.statistic = "{STATISTIC}"
    ORDER BY s1.mask_label, s1.datetime  ASC; """

records = pd.read_sql(sql, db)

st.dataframe(records)



# # query all tables from DB
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
# all_tables = cursor.fetchall()
# # conversion of list of tuples to list of strings
# all_tables = [''.join(i) for i in all_tables]
#
# # make tables selectable
# select_table = st.sidebar.selectbox('Select Table', all_tables)
#
# # display user-selected table
# sql_query = "SELECT * FROM {}".format(select_table)
# selected_table = pd.read_sql_query(sql_query, db)
# st.dataframe(selected_table)

# chart
charttable = records[["datetime", "value"]]
chart = altair.Chart(charttable).mark_circle().encode(x= "datetime", y="value")
st.altair_chart(chart)
cursor.close()
db.close()