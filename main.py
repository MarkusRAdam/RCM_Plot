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

#for row in cursor.execute('SELECT * FROM s1fieldstatistic;'):
#    print(row)

# create sider
st.sidebar.title('Radar Crop Monitor APP')
st.sidebar.markdown('_Short Description of the Project & Contributors ... _')
st.sidebar.markdown('#')
st.sidebar.markdown('#')
st.sidebar.header('Data Exploration')

# query all tables from DB
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()
# conversion of list of tuples to list of strings
all_tables = [''.join(i) for i in all_tables]

# make tables selectable
select_table = st.sidebar.selectbox('Select Table', all_tables)

# display user-selected table
sql_query = "SELECT * FROM {}".format(select_table)
selected_table = pd.read_sql_query(sql_query, db)
st.dataframe(selected_table)

# chart
charttable = pd.read_sql_query('SELECT * FROM s1fieldstatistic;', db)
charttable = charttable[["value", "datetime"]]
chart = altair.Chart(charttable).mark_circle().encode(x= "datetime", y="value")
st.altair_chart(chart)
cursor.close()
db.close()