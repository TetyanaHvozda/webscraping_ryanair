from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from datetime import datetime, timedelta
import time
import csv

# Path to your ChromeDriver
service = Service('')

# Start the browser
driver = webdriver.Chrome(service=service)

# List of destination airport codes
cities = [
    "ALC", "BCN", "IBZ", "MAD", "SVQ", "VLC", "AGP", "OPO", "LIS", "FAO",
    "KRK", "EIN", "BLQ", "NAP", "PMO", "RMI", "FCO", "DUB", "EDI", "STN",
    "MAN", "BVA", "MRS", "CGN"
]

# Get today's date and calculate the next days
start_date = datetime.now() + timedelta(days=1)
num_days = 3

# CSV file to store flight details
csv_filename = 'flight_data.csv'


# Function to scrape flight data for a specific route and date
def scrape_flights(origin, destination, date_out):
    # Build the URL dynamically for each route and date
    url = (f"https://www.ryanair.com/at/de/trip/flights/select?adults=1&teens=0&children=0&infants=0"
           f"&dateOut={date_out}&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false"
           f"&originIata={origin}&destinationIata={destination}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0"
           f"&tpStartDate={date_out}&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata={origin}"
           f"&tpDestinationIata={destination}")

    # Load the webpage
    driver.get(url)

    # Wait for the page to load
    time.sleep(10)

    # Try to find flight cards on the page
    flight_cards = driver.find_elements(By.CSS_SELECTOR, "flight-card-new")

    # List to store flight data for CSV
    flight_data = []

    if flight_cards:
        for card in flight_cards:
            try:
                # Extract departure time and arrival time
                departure_time = card.find_element(By.CSS_SELECTOR,
                                                   '[data-ref="flight-segment.departure"] .flight-info__hour').text
                arrival_time = card.find_element(By.CSS_SELECTOR,
                                                 '[data-ref="flight-segment.arrival"] .flight-info__hour').text

                # Extract origin and destination cities
                origin_city = card.find_element(By.CSS_SELECTOR,
                                                '[data-ref="flight-segment.departure"] .flight-info__city').text
                destination_city = card.find_element(By.CSS_SELECTOR,
                                                     '[data-ref="flight-segment.arrival"] .flight-info__city').text

                # Extract flight number
                flight_number = card.find_element(By.CSS_SELECTOR, '.card-flight-num__content').text

                # Extract origin and destination airports from attributes
                origin_airport = \
                    card.find_element(By.CSS_SELECTOR, '[data-ref="origin-airport__VIE"]').get_attribute(
                        'data-ref').split(
                        "__")[1]
                destination_airport = \
                    card.find_element(By.CSS_SELECTOR, '[data-ref^="destination-airport__"]').get_attribute(
                        'data-ref').split("__")[1]

                # Check if the flight is sold out
                sold_out = card.find_elements(By.CSS_SELECTOR, 'flights-lazy-sold-out-flight-card')
                if sold_out:
                    price = 'Ausverkauft'
                else:
                    # Extract the price if the flight is not sold out
                    price = card.find_element(By.CSS_SELECTOR, '.flight-card-summary__new-value').text

                # Append flight data as a row
                flight_data.append(
                    [flight_number, origin_city, origin_airport, destination_city, destination_airport,
                     date_out, departure_time, arrival_time, price])

            except Exception as e:
                print(f"Error extracting flight details: {e}")
    else:
        print(f"No flight cards found for {origin} to {destination} on {date_out}.")

    return flight_data


# Open the CSV file in write mode
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write header row
    writer.writerow(['Flight Number', 'Origin City', 'Origin Airport', 'Destination City', 'Destination Airport',
                     'Departure Date', 'Departure Time', 'Arrival Time', 'Price'])

    # Loop over each city as destination and scrape flights for the next 7 days
    origin = "VIE"  # Vienna airport code
    for destination in cities:
        for i in range(num_days):
            # Calculate the date for the specific day
            date_out = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

            # Scrape the flight data for the route and date
            flights = scrape_flights(origin, destination, date_out)

            # Write flight data to CSV
            for flight in flights:
                writer.writerow(flight)

    # Loop over each city as the origin and scrape flights for the next 7 days with Vienna as the destination
    destination = "VIE"  # Vienna as the destination
    for origin in cities:
        for i in range(num_days):
            # Calculate the date for the specific day
            date_out = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

            # Scrape the flight data for the reverse route and date
            flights = scrape_flights(origin, destination, date_out)

            # Write flight data to CSV
            for flight in flights:
                writer.writerow(flight)

# Close the browser after scraping is complete
driver.quit()

print(f"Flight data has been saved to {csv_filename}.")
