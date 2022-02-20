"""
Script for displaying time series of Radar backscatter and NDVI values from a database in a streamlit web app.

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

# Permanent database path can be defined in set_permanent_db_path() to avoid path query within the
# app on every app start.
# If you want to keep the app query functionality (default), please do not change permanent_db_path!


# define function to set permanent database path
def set_permanent_db_path():
    """
    Defines permanent path to database. Default "Enter path here" leads to path query in the web app.
    If default is replaced with valid database path, the path query will be avoided (main app page opens directly).

    :return: string with default or database path
    """
    permanent_db_path = "Enter path here"
    return permanent_db_path


# define function for establishing connection to database
def db_connect(db_path):
    """
    Tries connecting to database & gets dataframe of all table names (which will be empty if database path is invalid),
    prints error if connection is unsuccessful.

    :param db_path: string with path to database file
    :return: sqlite3.Connection object with connection to database, dataframe with table names
    """
    try:
        database = sqlite3.connect(db_path)
        table_names = pd.read_sql_query("SELECT * FROM sqlite_master WHERE type='table'", database)
        return database, table_names
    except sqlite3.Error as error:
        connection_error = "Error while connecting to database:" + str(error)
        st.error(connection_error)


def replace_strings(string_list, string_dict):
    """
    Can be used to convert list of strings in two ways:
    * searching if keys from dictionary are in list and replacing them with corresponding values
    * searching if values from dictionary are in list and replacing them with corresponding keys

    Direction of conversion is chosen automatically depending on whether keys or values from dictionary are in list

    :param string_list: list of strings
    :param string_dict: dictionary where keys and values are strings
    :return: potentially updated list of strings
    """

    updated_string_list = string_list.copy()

    # search for dict keys in input list and replace them with corresponding values
    for string in string_dict.keys():
        if string in updated_string_list:
            updated_string_list = [w.replace(string, string_dict.get(string)) for w in updated_string_list]

    # if keys have been found and replaced, new list differs from input list
    if updated_string_list != string_list:
        return updated_string_list

    # if no change occurred, search for values and replace them with corresponding keys
    else:
        for string in string_dict.values():
            if string in updated_string_list:
                matching_key_list = [key for key, value in string_dict.items() if value == string]
                matching_key = matching_key_list[0]
                updated_string_list = [w.replace(string, matching_key) for w in updated_string_list]
        return updated_string_list


# define function to add placeholder to multiselection tuple if len == 1 (prevents syntax error in sql query)
def placeholders(multiselections):
    """
    Adds placeholder string to tuples if their length is 1. This prevents a syntax error in the sql query.

    :param multiselections: tuple with user-selected multiselection filter values
    :return: tuple with filter values and optional placeholder
    """
    if len(multiselections) == 1:
        multiselections = multiselections + ("placeholder",)
        return multiselections
    else:
        return multiselections


# define function to make charts
def make_chart(pol_records, axis_label, domain, selection, color_column, sort, title, stat_button):
    """
    Creates scatterplot and trendline diagrams (based on LOESS or Rolling Mean) of VV/VH/NDVI values
    from respective subset of dataframe "records".
    Trendline is added to scatterplot if selected by user.

    :param pol_records: subset of dataframe "records" with one polarisation/value (VV,VH,NDVI)
    :param axis_label: string with y-axis label
    :param domain: numpy.ndarray with boundaries for x-axis (start and end date)
    :param selection: altair.selection_multi object with values that will be colored (bound to selection in chart legend) 
    :param color_column: dataframe column by which data points are colored in chart
    :param sort: list with order of values in chart legend
    :param title: string with chart title
    :param stat_button: string with name of trendline selected by user
    :return: altair.Chart object displaying either VV/VH/NDVI values (and trend line if selected)
    """
    # make the base chart (scatterplot with x=time, y=value)
    value_chart = alt.Chart(pol_records).mark_circle().encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22),
                scale=alt.Scale(domain=list(domain))),
        y=alt.Y("value", axis=alt.Axis(title=axis_label, titleFontSize=22)),
        color=alt.condition(selection, color_column, alt.value("lightgray"), sort=sort,
                            legend=alt.Legend(type='symbol')),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
        tooltip=("fid", "acquisition", "product")).add_selection(selection). \
        properties(title=title, width=1000, height=500)

    # make LOESS trendline chart
    loess_chart = alt.Chart(pol_records).encode(
        x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22),
                scale=alt.Scale(domain=list(domain))),
        y=alt.Y("value", axis=alt.Axis(title=axis_label, titleFontSize=22))).transform_filter(selection). \
        transform_loess("datetime", "value").mark_line(color="red")

    # make Rolling Mean trendline chart (mean of 10 values)
    mean_chart = alt.Chart(pol_records).mark_line(color="red").transform_filter(selection). \
        transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

    # add trendline to scatterplot, if selected
    if stat_button == "LOESS":
        final_chart = value_chart + loess_chart
    elif stat_button == "Rolling Mean":
        final_chart = value_chart + mean_chart
    else:
        final_chart = value_chart

    return final_chart


# define function to fill list of charts that will be displayed
def display_chart(vv_vh_ndvi, records, chart):
    """
    Displays chart in app if the corresponding parameter was selected by user and is available,
    returns warning if parameter was selected but is not available.

    :param vv_vh_ndvi: string with parameter (VV,VH,NDVI)
    :param records: dataframe with data that will be displayed
    :param chart: altair.Chart object displaying values with vv_vh_ndvi parameter
    :return: warning if no data is available for selected parameter
    """

    # if data with parameter is available
    if records["parameter"].str.contains(vv_vh_ndvi).any():
        st.altair_chart(chart.configure_title(fontSize=28).configure_legend(titleFontSize=20, labelFontSize=18))
    # if selection has been made, but no data with parameter available
    elif records.empty is False:
        param_warning = "No data available for parameter {}".format(vv_vh_ndvi)
        return st.warning(param_warning)


# define function for deploying main page of app
def main_part(db):
    """
    Deploys the main page of the app and its functionalities. This mainly includes:
    * setting app title and description
    * getting and displaying available data filter values from database, then getting filter selections from user
    * querying data as dataframe from database, based on filter values selected by user
    * making and displaying charts based on queried dataframe

    :param db: sqlite3.Connection object with connection to database
    :return: no return in script, but deploys streamlit app functionalities (filters, charts)
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

    # define dict of filter values that need to be converted from abbreviations to full words
    string_dict = {"DEMM": "Demmin", "FRIEN": "Frienstedt", "MRKN": "Markneukirchen",
                   "A": "Ascending", "D": "Descending"}

    # query unique values from specific table columns of db to use as selectable values for main and dependent filters
    # abbreviated values (in aoi/acquisition) are converted to full words with replace_strings()
    aoi_names = pd.read_sql_query('select distinct aoi from areaofinterest;', db)
    aoi_names = aoi_names["aoi"].tolist()
    aoi_names = replace_strings(aoi_names, string_dict)
    years = pd.read_sql_query("select distinct year from areaofinterest;", db)
    crop_types = pd.read_sql_query("select distinct crop_type from croplegend;", db)
    products = pd.read_sql_query("select distinct product from s1fieldstatistic;", db)
    acq_types = pd.read_sql_query("select distinct acquisition from s1fieldstatistic;", db)
    acq_types = acq_types["acquisition"].tolist()
    acq_types = replace_strings(acq_types, string_dict)
    parameter = pd.read_sql_query("select distinct polarization from s1fieldstatistic;", db)
    stats = pd.read_sql_query("select distinct statistic from s1fieldstatistic;", db)
    fid = pd.read_sql_query("select distinct fid from areaofinterest;", db)

    # get single value selections of main filters from user
    # full words (in aoi) are converted back to abbreviations for sql query
    aoi_selection = [st.sidebar.selectbox("AOI", aoi_names)]
    aoi_selection = replace_strings(aoi_selection, string_dict)
    aoi_selection = aoi_selection[0]
    year_selection = st.sidebar.selectbox("Year", years)
    crop_selection = st.sidebar.selectbox("Crop Type", crop_types)
    stat_selection = st.sidebar.selectbox("Statistic", stats)

    # print title for dependent filters in app
    st.sidebar.markdown('#')
    st.sidebar.header('Dependent Filter')

    # get tuples of multiselections (dependent filters) from user
    # full words (in acquisition) are converted back to abbreviations for sql query
    acq_selection = st.sidebar.multiselect("Acquisition Mode", acq_types)
    acq_selection = replace_strings(acq_selection, string_dict)
    acq_selection = tuple(acq_selection)
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
    sql_body = f"""SELECT 
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
    records = pd.read_sql(sql_body, db)

    # print warning when no filter is selected and error when invalid filter combination (with no data) is selected
    if records.empty:
        if any(len(x) == 0 for x in dependent_selections):
            st.warning("No selection has been made. Please select filter combination.")
        else:
            st.error("No data is available for this filter combination. Please select other filter combinations.")

    # create time slider for date range selection (start and end date of x-axis of charts)

    # convert datetime string column to datetime
    records["datetime"] = pd.to_datetime(records['datetime']).apply(lambda x: x.date())

    # get earliest and latest date from dataframe as boundaries for slider
    start_date = records["datetime"].min()
    end_date = records["datetime"].max()

    st.markdown("#")

    # define expander box which will contain time slider and radiobuttons for trendline and coloring selection
    with st.expander("Additional filter", expanded=True):

        # define slider values from user selection and filter dataframe based on these values
        try:
            st.subheader("Select date range")
            slider_1, slider_2 = st.slider('', value=(start_date, end_date), format="DD.MM.YY")
            records = records[(records['datetime'] >= slider_1) & (records['datetime'] <= slider_2)]
        except KeyError:
            st.warning("Date range slider is only available after a valid filter combination has been selected")

        st.markdown("#")

        # make columns for trendline/fid selection buttons
        col1, col2 = st.columns(2)

        # make button for selection of trendline type
        col1.subheader("Select trendline")
        stat_button = col1.radio("", ("None", "LOESS", "Rolling Mean"))

        # make button for selection of coloring column
        col2.subheader("Select data point coloring")
        color_button = col2.radio("", ("by FID", "by Acquisiton Mode"))

    st.markdown("#")

    # create charts (scatterplots and trendlines (LOESS/Rolling mean)) for VV, VH and NDVI values

    # remap acquisition values from abbreviations (A/D) to full words (ascending/descending)
    records["acquisition"] = records["acquisition"].map({"A": "ascending", "D": "descending"})

    # set dataframe column by which points are colored in charts (acquisition or FID)
    if color_button == "by FID":
        color_selection = alt.selection_multi(fields=['fid'], bind='legend')
        color_column = "fid"
        sort = None
    else:
        color_selection = alt.selection_multi(fields=['acquisition'], bind='legend')
        color_column = "acquisition"
        sort = ["D"]

    # get earliest and latest date again from potentially time-filtered dataframe
    start_date = records["datetime"].min()
    end_date = records["datetime"].max()

    # set domain containing earliest and latest date in dataframe, used as boundaries for x-axis of charts
    domain_pd = pd.to_datetime([start_date, end_date]).view("int64") / 10 ** 6

    # set y-axis label based on user-selected statistic (which can be in units or absolute values)
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

    # go through selected parameters, create dataframe subset with parameter
    # and make/display corresponding charts, if data is available
    for param in param_selection:
        if param == "VV":
            vv_records = records[records["parameter"] == "VV"]
            vv_chart = make_chart(vv_records, y_axis_label_db, domain_pd, color_selection,
                                  color_column, sort, vv_title, stat_button)
            display_chart("VV", records, vv_chart)
        if param == "VH":
            vh_records = records[records["parameter"] == "VH"]
            vh_chart = make_chart(vh_records, y_axis_label_db, domain_pd, color_selection,
                                  color_column, sort, vh_title, stat_button)
            display_chart("VH", records, vh_chart)
        if param == "NDVI":
            ndvi_records = records[records["parameter"] == "NDVI"]
            ndvi_chart = make_chart(ndvi_records, y_axis_label_ndvi, domain_pd, color_selection,
                                    color_column, sort, ndvi_title,
                                    stat_button)
            display_chart("NDVI", records, ndvi_chart)

    # close connection to db
    db.close()


# define function to get path to database from user, check if path is valid and deploy main app page
def db_path_query():
    """
    First checks if permanent database path has been set in set_permanent_db_path().
    If yes, it checks if this path is valid and tries connecting to database with db_connect().
    If no, it queries path from user in the app and tries connection with entered path.
    Path validity is checked by checking path ending (must be ".db") and
    table_names (which is empty if path is invalid).
    After connection with valid path is established, the main web app page/functionality
    is deployed by executing main_part().
    """
    # get permanent database path (or default string)
    permanent_db_path = set_permanent_db_path()

    # if path has not been set in script (= default)
    if permanent_db_path == "Enter path here":
        st.set_page_config(layout="wide")
        text_input_container = st.empty()
        path = text_input_container.text_input("Please enter path to database (including file name): ")
        if path != "" and path.endswith(".db") is False:
            st.error("Entered path does not contain a valid database")
        elif path.endswith(".db"):
            database, table_names = db_connect(path)
            if table_names.empty:
                st.error("Entered path does not contain a valid database")
            else:
                text_input_container.empty()
                main_part(database)

    # if path has been set in script
    else:
        if permanent_db_path.endswith(".db"):
            database, table_names = db_connect(permanent_db_path)
            if table_names.empty:
                st.error("Permanent database path does not contain a valid database")
            else:
                st.set_page_config(layout="wide")
                main_part(database)
        else:
            st.error("Permanent database path does not contain a valid database")


if __name__ == "__main__":
    db_path_query()
