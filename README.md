# COVID-19 Monitor Germany
## Descritption
The COVID-19 Monitor Germany is an interactive dashboard to give a better overview about the pandemic situation in 
Germany. It provides a multitude of plots and daily calculated figures. 

The data used come from official sources. On the one hand from the 
[Robert-Koch-Institut (RKI)](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/nCoV_node.html;jsessionid=CAD4005C4258999326E52AD7193F1109.internet061),
on the other hand from the [Intensivregister](https://www.intensivregister.de/#/aktuelle-lage/reports). The 
Intensivregister provides data on the situation in intensive care units in Germany.

Since there are strong fluctuations in the reported numbers (fewer reports on weekends, fewer tests on weekends, etc.), 
smoothing in the form of 7-day moving averages is used to better show a trend. Also in the daily overview, the attention 
is shown on the trend analysis in the form of 7-day moving averages, rather than on the daily reported figures. They are 
nevertheless displayed for the sake of completeness.

[Plotly Dash](https://dash.plotly.com/) was used to generate the interactive plots.

![COVID-19 Monitor Germany in Action](img/covid19_monitor_germany.gif)


## Plots and Figures
The plots are divided into the three groups "daily overview", "corona cases" and "intensive care". The three groups can 
be selected via the tabs with the same names.

#### Daily Overview
* reported cases of last day 
* reported deaths of last day
* R0 of last day
* figures of last 7 days
* new reported deaths by reporting date (start of illness, alternativeliy reporting date)
* delay in reporting between public health departments and the RKI


#### Corona Cases
* cases reported by RKI
* total reported cases by reference date (start of illness, alternativeliy reporting date)
* deaths reported by RKI
* total reported deaths by reference date (start of illness, alternativeliy reporting date)
* R0 and daily proportional change
* 7 day incidence
* Number of PCR tests
* Clinical aspects
* distribution of inhabitants and deaths
* distribution of reported cases and deaths in relation to inhabitants

#### Intensive care
* number of reporting areas
* new admissions of COVID-19 patients to intensive care unit since day before
* change from previous day of intensive care beds occupied by COVID-19 patients
* Proportion of COVID-19 patients receiving intensive care and ventilation
* intensive care beds occupied with and without COVID-19 patients
* intensive care beds proportional figures


## Usage of interactive Plots
#### Zoom
You can zoom in and out of the plot by clicking the corresponding buttons on the right upper corner of a plot. You can 
also select an area to zoom in by selecting the beginning of the area by clicking on the left mouse button and holding
it. 
#### Unselect plots in a graph
You can unselect the plot by clicking the corresponding name in the plot legend. Clicking the name again displays the 
plot again.
#### Show only one plot
By double-clicking on the specific plot name in the legend, this plot can be selected individually. By double-clicking 
on the name again, all plots are displayed again.


## Installation
One dependency is ```pdftotext```. Because of this you have to make sure that you have ```poppler``` installed. For Mac 
you can run

```
brew install pkg-config poppler
```

on your terminal. For other OS see [here](https://pypi.org/project/pdftotext/).

 First install the virtual environment within the dashboard folder. open your terminal and navigate to the project's
  directory. 
````
pipenv install
````
This will install all the required Python packages from the Pipfile and create a virtual pipenv environment.

## Run the app
On your terminal in the dashboard directory run

```
pipenv run python app.py
```

This starts a local server. The terminal displays the `IP-Address` to access the app in your browser. Locally and by
 default it should be 
 
 ```
http://127.0.0.1:8050/
```

If you want to use ```gunicorn```, e.g. for production, run in your terminal not the first command, but
```
pipenv run gunicorn app:server -b localhost:8000
```
. Now you can find the app under
```
http://127.0.0.1:8000/
```

## Run automatic update of data
This project has a script called ```update_data.py```, which performes the updates for all used data sources. In the 
main folder also exists a shell-script called ```update_data.sh```. Inside this script you have to change to path to 
your project folder. Then you can create a cron job to run the script every 10 minutes, for example. To get this script
running every 10 minutes on a mac, go to Terminal and use the command

```crontab -e```.

Inside the opened file you have to define the time frame of the update and the path to the script. You can pipe the 
output into a log file. You can do it with

```*/10 * * * * /path/to/your/project/folder/update_data.sh >> /path/to/your/project/folder/update_data.log 2>&1```.

## Contributors
[Daniel Haake](https://www.linkedin.com/in/daniel-haake/): Dashboard Application, Data Collection, Data Preparation, 
Data Analysis & Visualization

[Christian Kirifidis](https://www.linkedin.com/in/christian-kirifidis/): Dashboard Application & Visualization

## License
The software is available under licence conditions of [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0).