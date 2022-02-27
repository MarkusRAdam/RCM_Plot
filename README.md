# RCM_Plot
This python tool can be used to run a streamlit web app that displays time series plots of Radar backscatter and NDVI values from a database. It was developed to work with a specific database containing data from the Radar Crop Monitor project. 

## Installation
### With Anaconda
If you are using Anaconda you can use the provided environment.yml file to set up a virtual environment in which the main script can be run. 
By default, the created environment will be named "RCM_Plot". You can change the name in the environment.yml file before setting up the environment.

Open the Anaconda prompt, make sure the environment.yml is in the specified directory, and enter the following:
```
conda env create -f environment.yml
```

Activate the created environment by entering:
```
conda activate <name_of_environment>
```

Then run the main.py script by entering:
```
streamlit run <path_to_main.py>
```
<br>
The web app should now open automatically in your default browser.
<br>

### Without Anaconda
If you are not using Anaconda, you have to manually install the packages that are imported in main.py (except sqlite3) and then run the script as described above.
<br>

## Web-App Features
By default, the app starts with an interface in which the path to the database has to be entered. You can bypass this interface by setting a permanent path in main.py. The app will then start directly with the main page.
<br>
The filter combination chosen here as an example, which certainly contains data and thus generates graphs, is as follows:
<br>
AOI (FRIEN), Year (2017), Crop Type (Winter Wheat), Statistic (Median), Acquisition Mode (A, D), Product (GRD, S2MSI2A), Parameter (VH, VV, NDVI), FID (4).
<br>

![webapp_final](https://user-images.githubusercontent.com/80339685/155840913-adf290b7-96e9-4ce2-bd44-90996c6e3a09.jpg)
_Resulting Web-App_

<br>
The desired filters can now be set on the left-hand side. 
<br>
It is also possible to filter the data set by date using the time slider and to insert statistical trend lines in the graphs. 
<br>
The data points can be coloured according to their FID or acquisition, as desired. 
<br>

## Documentation
The documentation of the functions can be found [here](https://rcm-plot.readthedocs.io/en/latest/#) 
