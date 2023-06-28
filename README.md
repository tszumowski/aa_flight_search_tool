# AA Award Flight Search Tool

## Description

This script scrapes the American Airlines (AA) award flight search page to find flight availability for multiple origin/destination pairs and dates. It's designed to provide a search tool in a context where AA has recently moved to dynamic pricing. In addition to the base search functionality, it offers the ability to filter results based on departure time, duration, number of stops, and number of miles.

The script leverages Python's `Selenium` package to access the web content and `BeautifulSoup` for parsing the HTML content. Data processing and manipulation is performed using `pandas`, `datetime` and `argparse` packages.

Please note that scraping websites should only be done respecting the terms of service of the website being scraped.

At the time of writing, the robots.txt for www.aa.com was:

```
User-agent: *
Disallow: /i18n/travelInformation/destinationInformation/venice/
Disallow: /i18n/AAdvantage/
Disallow: /i18n/aboutUs
Disallow: /i18n/agencyPrograms
Disallow: /i18n/airportAndLounge
Disallow: /i18n/amrcorp
Disallow: /i18n/businessPrograms
Disallow: /i18n/contactAA
Disallow: /i18n/customerService
Disallow: /i18n/disclaimers
Disallow: /i18n/productsGifts
Disallow: /i18n/promo
Disallow: /i18n/urls
Disallow: /i18n/utility
Disallow: /contactAA/viewEmailFormAccess.do?eventName=lowFare
Disallow: /pubcontent/jba
Disallow: /pubcontent/jbax
```

The URL used in this script is allowed based on that robots.txt.

## Installation

To install the required Python packages, run the following command:

```
pip install argparse pandas beautifulsoup4 selenium tabulate
```

Make sure you have `chromedriver` installed and available in your system's `PATH` for Selenium to use.

## Usage

You can run the script using Python as follows:

```
python search_aa_award_flights.py --help
```

It accepts the following command-line arguments:

* `depart_date`: Departure date(s) in `YYYY-MM-DD` format. This is a required argument.
* `origin`: Origin airport code. This is a required argument.
* `destination`: Destination airport code. This is a required argument.
* `n_adults`: Number of adults. This is a required argument.
* `n_children`: Number of children. This is a required argument.
* `--max_miles_main`: Maximum number of miles in thousands. Default value is 20.
* `--max_duration`: Maximum duration of flight in minutes. Default value is 660 minutes (11 hours).
* `--depart_time_range`: Departure time range in `HH:MM` format. Default value is `07:00` to `16:00`.
* `--arrive_time_range`: Arrival time range in `HH:MM` format. Default value is `12:00` to `22:00`.
* `--max_stops`: Maximum number of stops. Default value is 1.
* `--output_file_raw`: Output file for raw flight data. Default is `flights_all.csv`.
* `--output_file_filtered`: Output file for filtered flight data. Default is `flights_filtered.csv`.
* `--sleep_init_sec`: Initial sleep time in seconds when loading browser. Default value is 10.
* `--sleep_sec`: Sleep time in seconds between each page load. Default value is 5.

Example:


```bash
python search_aa_award_flights.py \
    --depart_date 2023-07-07 2023-07-08 \
    --origin SLC RAP \
    --destination EWR PHL \
    --n_adults 1 \
    --n_children 1 \
    --max_miles_main 20 \
    --max_duration 600 \
    --depart_time_range 07:00 16:00 \
    --arrive_time_range 12:00 22:00 \
    --max_stops 1 \
    --output_file_raw flights_all.csv
```

## Output

The script will generate two output files: one for the raw scraped flight data, and another for the flight data after applying the specified filters. These are CSV files, and their default names are `flights_all.csv` and `flights_filtered.csv` respectively.

The CSV files will contain information on origin, destination, departure time, arrival time, flight duration, number of stops, and the number of miles required for each cabin type (main, business, first). 

## Limitations

As the script scrapes the AA award search page, its performance will be determined by the response time of the website and your internet connection. The script is not the fastest due to this limitation. Please also note that the structure of the website may change over time, and this script may no longer work at that point. It is not being actively maintained.


## Example Output

This is an output using the example above.

```
python search_aa_award_flights.py \
    --depart_date 2023-07-07 2023-07-08 \
    --origin SLC RAP \
    --destination EWR PHL \
    --n_adults 1 \
    --n_children 1 \
    --max_miles_main 20 \
    --max_duration 600 \
    --depart_time_range 07:00 16:00 \
    --arrive_time_range 12:00 22:00 \
    --max_stops 1 \
    --output_file_raw flights_all.csv

Arguments:
{'arrive_time_range': ['12:00', '22:00'],
 'depart_date': ['2023-07-07', '2023-07-08'],
 'depart_time_range': ['07:00', '16:00'],
 'destination': ['EWR', 'PHL'],
 'max_duration': 600,
 'max_miles_main': 20,
 'max_stops': 1,
 'n_adults': 1,
 'n_children': 1,
 'origin': ['SLC', 'RAP'],
 'output_file_filtered': 'flights_filtered.csv',
 'output_file_raw': 'flights_all.csv',
 'sleep_init_sec': 10,
 'sleep_sec': 5}


Scraping 1 of 8: 2023-07-07, SLC, EWR
Found 40 flights
Found 40 total flights.
Found 6 flights that meet the criteria.

Scraping 2 of 8: 2023-07-07, SLC, PHL
Found 40 flights
Found 40 total flights.
Found 1 flights that meet the criteria.

Scraping 3 of 8: 2023-07-07, RAP, EWR
Found 39 flights
Found 39 total flights.
Found 0 flights that meet the criteria.

Scraping 4 of 8: 2023-07-07, RAP, PHL
Found 40 flights
Found 40 total flights.
Found 0 flights that meet the criteria.

Scraping 5 of 8: 2023-07-08, SLC, EWR
Found 40 flights
Found 40 total flights.
Found 0 flights that meet the criteria.

Scraping 6 of 8: 2023-07-08, SLC, PHL
Found 40 flights
Found 40 total flights.
Found 1 flights that meet the criteria.

Scraping 7 of 8: 2023-07-08, RAP, EWR
Found 40 flights
Found 40 total flights.
Found 0 flights that meet the criteria.

Scraping 8 of 8: 2023-07-08, RAP, PHL
Found 40 flights
Found 40 total flights.
Found 0 flights that meet the criteria.
Done scraping.
Found 319 total flights.
Found 8 flights that meet the criteria.
+--------+-------------+-------------+-------------+----------+-----------+----------------+-----------------+------------+
| origin | destination | depart_time | arrive_time | duration | num_stops | num_miles_main | num_miles_first |    date    |
+--------+-------------+-------------+-------------+----------+-----------+----------------+-----------------+------------+
|  SLC   |     LGA     |  07:42:00   |  16:59:00   |   437    |     1     |      14.0      |      31.0       | 2023-07-07 |
|  SLC   |     JFK     |  07:42:00   |  19:29:00   |   587    |     1     |      16.0      |      68.5       | 2023-07-07 |
|  SLC   |     LGA     |  07:42:00   |  19:30:00   |   588    |     1     |      15.5      |      29.5       | 2023-07-07 |
|  SLC   |     PHL     |  08:26:00   |  17:48:00   |   442    |     1     |      19.5      |      29.5       | 2023-07-07 |
|  SLC   |     LGA     |  09:30:00   |  20:40:00   |   550    |     1     |      19.5      |      33.5       | 2023-07-07 |
|  SLC   |     EWR     |  11:19:00   |  20:17:00   |   418    |     1     |      18.5      |      32.5       | 2023-07-07 |
|  SLC   |     LGA     |  12:11:00   |  22:00:00   |   469    |     1     |      18.5      |      54.5       | 2023-07-07 |
|  SLC   |     PHL     |  09:30:00   |  21:18:00   |   588    |     1     |      18.5      |      28.5       | 2023-07-08 |
+--------+-------------+-------------+-------------+----------+-----------+----------------+-----------------+------------+
Saved 8 records to flights_filtered.csv.
Saved 319 records to flights_all.csv.
```
