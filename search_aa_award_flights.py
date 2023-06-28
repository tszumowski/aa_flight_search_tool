"""
Script to search for AA award availablity for multiple origin/destination pairs
and dates. It lets you filter on departure time, duration, number of stops, 
and number of miles. 

At the time of writing, there were plenty of award search tools out there, but
AA just recently moved to dynamic pricing, so there weren't any that could 
filter on dynamic pricing.

This script uses Selenium to scrape the AA award search page. It's not the
fastest, but it works.

Usage:
    python search_aa_award_flights.py --help
"""

import argparse
import datetime
import itertools
import pandas as pd
import re
import time

from bs4 import BeautifulSoup
from pprint import pprint
from selenium import webdriver
from typing import Any, Dict, List, Tuple
from tabulate import tabulate


def process_flights(flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed_flights = []

    for flight in flights:
        processed_flight = {}

        # Process origin, destination, depart_time, and arrive_time
        processed_flight["origin"] = flight["origin"]
        processed_flight["destination"] = flight["destination"]

        # Convert depart_time and arrive_time to datetime.time objects
        depart_time = datetime.datetime.strptime(
            flight["depart_time"], "%I:%M %p"
        ).time()
        arrive_time = datetime.datetime.strptime(
            flight["arrive_time"], "%I:%M %p"
        ).time()
        processed_flight["depart_time"] = depart_time
        processed_flight["arrive_time"] = arrive_time

        # Process duration
        duration_parts = re.findall(r"\d+", flight["duration"])
        duration_minutes = int(duration_parts[0]) * 60 + int(duration_parts[1])
        processed_flight["duration"] = duration_minutes

        # Process num_stops
        processed_flight["num_stops"] = int(flight["num_stops"].split(" ")[0])

        # Process miles
        num_miles = {}
        for cabin, miles in flight["num_miles"].items():
            cabin = cabin.lower()
            if "main" in cabin:
                cabin = "main"
            elif "first" in cabin:
                cabin = "first"
            elif "business" in cabin:
                cabin = "business"

            miles_value = float(miles.replace("K", ""))
            num_miles[cabin] = miles_value

        # Unpack to num_miles_X, where X is each key
        for cabin, miles in num_miles.items():
            processed_flight[f"num_miles_{cabin}"] = miles

        processed_flights.append(processed_flight)

    # sort by ascending depart_time
    processed_flights.sort(key=lambda x: x["depart_time"])

    return processed_flights


def scrape_flight_page(url: str, driver: webdriver.Chrome, sleep_sec: int = 10) -> list:
    """
    Scrapes the AA award flight page for flight details and number of miles for each cabin type.

    Args:
        url: URL of the AA award flight page to scrape.
        driver: Selenium webdriver to use to fetch the page.

    Returns:
        flights: List of dictionaries containing flight details and number of miles for each cabin type.
    """
    # fetch the page
    driver.get(url)

    # wait N seconds
    if sleep_sec:
        time.sleep(sleep_sec)

    # get the page source
    html = driver.page_source

    # in the html, scrape flights
    soup = BeautifulSoup(html, "html.parser")

    # Find all elements that correspond to a flight
    flight_elements = soup.find_all(
        "div", class_="grid-x grid-padding-x ng-star-inserted"
    )

    # Initialize an empty list to store flight details
    flights = []

    # Iterate through each flight element and extract necessary information
    print(f"Found {len(flight_elements)} flights")
    for flight in flight_elements:
        # Extract origin, destination, depart_time, arrive_time, duration and num_stops
        origin = (
            flight.find("div", class_="cell large-3 origin")
            .find("div", class_="city-code")
            .text.strip()
        )
        depart_time = (
            flight.find("div", class_="cell large-3 origin")
            .find("div", class_="flt-times")
            .text.strip()
        )
        destination = (
            flight.find("div", class_="cell large-3 destination")
            .find("div", class_="city-code")
            .text.strip()
        )
        arrive_time = (
            flight.find("div", class_="cell large-3 destination")
            .find("div", class_="flt-times")
            .text.strip()
        )
        duration = flight.find("div", class_="duration").text.strip()
        num_stops = flight.find("div", class_="stops").text.strip()

        # Find all cabin types and corresponding number of miles within this flight
        cabin_elements = flight.find_all(
            "div", class_="cell auto pad-left-xxs pad-right-xxs ng-star-inserted"
        )

        # Initialize an empty dictionary to store cabin type and corresponding number of miles
        cabin_miles = {}

        # Iterate through each cabin element and extract necessary information
        for cabin in cabin_elements:
            cabin_type = cabin.find(
                "span", class_="hidden-accessible hidden-product-type"
            )
            num_miles = cabin.find("span", class_="per-pax-amount ng-star-inserted")

            # If both a cabin type and number of miles are found, add them to the dictionary
            if cabin_type is not None and num_miles is not None:
                cabin_miles[cabin_type.text.strip()] = num_miles.text.strip()

        # Append this flight's details and number of miles for each cabin type to the list of flights
        flights.append(
            {
                "origin": origin,
                "destination": destination,
                "depart_time": depart_time,
                "arrive_time": arrive_time,
                "duration": duration,
                "num_stops": num_stops,
                "num_miles": cabin_miles,
            }
        )

    # Cleanup
    flights = process_flights(flights)

    return flights


def filter_flights(
    flights: List[Dict[str, Any]],
    max_miles_main: int,
    max_duration: int,
    depart_time_range: Tuple[datetime.time, datetime.time],
    arrive_time_range: Tuple[datetime.time, datetime.time],
    max_stops: int,
) -> List[Dict[str, Any]]:
    """
    Filters a list of flights based on various criteria.

    Args:
        flights: List of dictionaries containing flight details and number of miles for each cabin type.
        max_miles_main: Maximum number of miles allowed for a flight in the main cabin.
        max_duration: Maximum duration of a flight in minutes.
        depart_time_range: Tuple of minimum and maximum departure times allowed for a flight.
        arrive_time_range: Tuple of minimum and maximum arrival times allowed for a flight.
        max_stops: Maximum number of stops allowed for a flight.

    Returns:
        filtered_flights: List of dictionaries containing flight details and number of miles for each cabin type that meet the filtering criteria.
    """
    filtered_flights = []

    # fix times
    min_depart_time, max_depart_time = depart_time_range
    min_arrive_time, max_arrive_time = arrive_time_range

    for flight in flights:
        num_miles_main = flight.get("num_miles_main", 10000000)
        if (
            num_miles_main <= max_miles_main
            and flight["duration"] <= max_duration
            and flight["depart_time"] >= min_depart_time
            and flight["depart_time"] <= max_depart_time
            and flight["arrive_time"] >= min_arrive_time
            and flight["arrive_time"] <= max_arrive_time
            and flight["num_stops"] <= max_stops
        ):
            filtered_flights.append(flight)

    return filtered_flights


def generate_url(
    depart_date: str,
    origin: str,
    destination: str,
    n_adults: int,
    n_children: int,
) -> str:
    """
    Generates the URL for the AA award flight page.

    Args:
        depart_date: Departure date in YYYY-MM-DD format.
        origin: Origin airport code.
        destination: Destination airport code.
        n_adults: Number of adults.
        n_children: Number of children.

    Returns:
        url: URL of the AA award flight page to scrape.

    """
    n_passengers = n_adults + n_children
    url = f"https://www.aa.com/booking/search?locale=en_US&pax={n_passengers}&adult={n_adults}&child={n_children}&type=OneWay&searchType=Award&cabin=&carriers=ALL&slices=%5B%7B%22orig%22:%22{origin}%22,%22origNearby%22:true,%22dest%22:%22{destination}%22,%22destNearby%22:true,%22date%22:%22{depart_date}%22%7D%5D&maxAwardSegmentAllowed=2"
    return url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search for AA award availability for multiple origin/destination pairs and dates."
    )
    parser.add_argument(
        "-d",
        "--depart_date",
        nargs="+",
        help="Departure date(s) in YYYY-MM-DD format.",
        required=True,
    )
    parser.add_argument(
        "-o", "--origin", nargs="+", help="Origin airport codes.", required=True
    )
    parser.add_argument(
        "-des",
        "--destination",
        nargs="+",
        help="Destination airport codes.",
        required=True,
    )
    parser.add_argument("--n_adults", type=int, help="Number of adults.", default=1)
    parser.add_argument("--n_children", type=int, help="Number of children.", default=0)
    parser.add_argument(
        "--max_miles_main",
        type=int,
        default=20,
        help="Maximum number of miles in thousands.",
    )
    parser.add_argument(
        "--max_duration",
        type=int,
        default=11 * 60,
        help="Maximum duration of flight in minutes.",
    )
    parser.add_argument(
        "--depart_time_range",
        nargs=2,
        default=["07:00", "16:00"],
        help="Departure time range in HH:MM format.",
    )
    parser.add_argument(
        "--arrive_time_range",
        nargs=2,
        default=["12:00", "22:00"],
        help="Arrival time range in HH:MM format.",
    )
    parser.add_argument(
        "--max_stops", type=int, default=1, help="Maximum number of stops."
    )
    parser.add_argument(
        "--output_file_raw",
        default="flights_all.csv",
        help="Output file for raw flight data.",
    )
    parser.add_argument(
        "--output_file_filtered",
        default="flights_filtered.csv",
        help="Output file for filtered flight data.",
    )
    parser.add_argument(
        "--sleep_init_sec",
        type=int,
        default=10,
        help="Initial sleep time in seconds when loading browser.",
    )
    parser.add_argument(
        "--sleep_sec",
        type=int,
        default=5,
        help="Sleep time in seconds between each page load.",
    )
    args = parser.parse_args()
    print("Arguments:")
    pprint(vars(args))

    # Flight info
    depart_date = args.depart_date
    origin = args.origin
    destination = args.destination
    n_adults = args.n_adults
    n_children = args.n_children

    # Filter criteria
    max_miles_main = args.max_miles_main  # in thousands
    max_duration = args.max_duration  # in minutes
    depart_time_range = tuple(
        datetime.datetime.strptime(d, "%H:%M").time() for d in args.depart_time_range
    )
    arrive_time_range = tuple(
        datetime.datetime.strptime(d, "%H:%M").time() for d in args.arrive_time_range
    )
    max_stops = args.max_stops

    # Other config
    output_file_raw = args.output_file_raw
    output_file_filtered = args.output_file_filtered
    sleep_init_sec = args.sleep_init_sec
    sleep_sec = args.sleep_sec

    # use chrome driver
    driver = webdriver.Chrome()
    time.sleep(sleep_init_sec)

    # loop through all of depart_date, origin, and destination combos.. including a counter
    all_flights = []
    all_filtered_flights = []
    error_combos = []
    missing_combos = []
    for i, (dt, o, d) in enumerate(itertools.product(depart_date, origin, destination)):
        # print the current iteration out of total iterations to keep track of progress
        print(
            f"\nScraping {i+1} of {len(depart_date) * len(origin) * len(destination)}: {dt}, {o}, {d}"
        )

        # generate the url
        url = generate_url(
            dt,
            o,
            d,
            n_adults,
            n_children,
        )

        # scrape the flights
        flights = []
        filtered_flights = []
        try:
            flights = scrape_flight_page(url, driver, sleep_sec=sleep_sec)
        except:
            print("Error scraping. Continuing to next iteration.")
            error_combos.append((dt, o, d))
            continue
        print(f"Found {len(flights)} total flights.")

        if len(flights) == 0:
            print("No flights found. Continuing to next iteration.")
            missing_combos.append((dt, o, d))
            continue

        # add the date to each object
        for flight in flights:
            flight["date"] = dt

        # filter the flights
        if len(flights) > 0:
            filtered_flights = filter_flights(
                flights,
                max_miles_main,
                max_duration,
                depart_time_range,
                arrive_time_range,
                max_stops,
            )
            print(f"Found {len(filtered_flights)} flights that meet the criteria.")

            all_flights.extend(flights)

        if len(filtered_flights) > 0:
            all_filtered_flights.extend(filtered_flights)

    print("Done scraping.")
    print(f"Found {len(all_flights)} total flights.")
    print(f"Found {len(all_filtered_flights)} flights that meet the criteria.")

    # Sort all by ascending origin, then ascending date, then ascending time
    all_filtered_flights = sorted(
        all_filtered_flights, key=lambda x: (x["origin"], x["date"], x["depart_time"])
    )

    # print in a pretty table
    print(
        tabulate(
            all_filtered_flights,
            headers="keys",
            tablefmt="pretty",
            showindex="never",
            floatfmt=".2f",
        )
    )

    # Save to CSV
    if len(all_filtered_flights) > 0:
        df = pd.DataFrame(all_filtered_flights)
        df.to_csv(output_file_filtered, index=False)
        print(f"Saved {len(all_filtered_flights)} records to {output_file_filtered}.")
    if len(all_flights) > 0:
        df = pd.DataFrame(all_flights)
        df.to_csv(output_file_raw, index=False)
        print(f"Saved {len(all_flights)} records to {output_file_raw}.")

    # print errors
    if len(error_combos) > 0:
        print("\nErrors:")
        pprint(error_combos)

    if len(missing_combos) > 0:
        print("\nMissing:")
        pprint(missing_combos)
