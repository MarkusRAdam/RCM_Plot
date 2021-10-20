import streamlit as st
import pandas as pd
#import sqlalchemy
import sqlite3
import datetime

try:
    db = sqlite3.connect('C:/Users/Laura/Desktop/UNI/2.Semester/Python_Teil_II/Abschlussprojekt/students_db_sql_queries_3/RCM_work.db')
    #db = sqlite3.connect('C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db')
    cursor = db.cursor()
    print("Database created and Successfully Connected to SQLite")
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)

#for row in cursor.execute('SELECT * FROM s1fieldstatistic;'):
#    print(row)

# create sider
st.sidebar.title('Radar Crop Monitor APP')
st.sidebar.markdown('_Display of SAR Parameters for Crop Monitoring _')
st.sidebar.markdown('_Contributors: Markus Adam & Laura Walder_')
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


# select area of interest

aoi = pd.read_sql_query('select name from aoilegend;', db)

aoi_select = aoi['name'].drop_duplicates()
            
options = st.multiselect(
    'Select your area of interest (AOI):',
    aoi_select)

st.write(type(options))
                

# datetime filter
message = 'Datetime Filter' 
# df = dataframe, in dem Fall s1fieldstatistics???
s1 = pd.read_sql_query('select distinct datetime from s1fieldstatistic;', db)
def df_filter(message,s1):

        slider_1, slider_2 = st.slider('%s' % (message),0,len(s1)-1,[0,len(s1)-1],1)

        while len(str(df.iloc[slider_1][1]).replace('.0','')) < 4:
            df.iloc[slider_1,1] = '0' + str(df.iloc[slider_1][1]).replace('.0','')
            
        while len(str(df.iloc[slider_2][1]).replace('.0','')) < 4:
            s1.iloc[slider_2,1] = '0' + str(df.iloc[slider_1][1]).replace('.0','')

        start_date = datetime.datetime.strptime(str(s1.iloc[slider_1][0]).replace('.0','') + str(s1.iloc[slider_1][1]).replace('.0',''),'%Y%m%d%H%M%S')
        start_date = start_date.strftime('%d %b %Y, %I:%M%p')
        
        end_date = datetime.datetime.strptime(str(s1.iloc[slider_2][0]).replace('.0','') + str(s1.iloc[slider_2][1]).replace('.0',''),'%Y%m%d%H%M%S')
        end_date = end_date.strftime('%d %b %Y, %I:%M%p')

        st.info('Start: **%s** End: **%s**' % (start_date,end_date))
        
        filtered_s1 = s1.iloc[slider_1:slider_2+1][:].reset_index(drop=True)
        
        print(filtered_s1)
        return filtered_s1

#st.slider(label, min_value, max_value, [0,len(df)-1], step)
slider_1, slider_2 = st.slider('%s' % (message),0,len(s1)-1,[0,len(s1)-1],1)
while len(str(s1.iloc[slider_1][1]).replace('.0','')) < 4:
    s1.iloc[slider_1,1] = '0' + str(s1.iloc[slider_1][1]).replace('.0','')
start_date = datetime.datetime.strptime(str(s1.iloc[slider_1][0]).replace('.0','') + str(s1.iloc[slider_1][1]).replace('.0',''),'%Y%m%d%H%M%S')
start_date = start_date.strftime('%d %b %Y, %I:%M%p')
st.info('Start: **%s** End: **%s**' % (start_date,end_date))
filtered_s1 = s1.iloc[slider_1:slider_2+1][:].reset_index(drop=True)


cursor.close()
db.close()