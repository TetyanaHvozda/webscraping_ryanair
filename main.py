from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from datetime import datetime, timedelta
import time
import mysql.connector

# Path to your ChromeDriver
service = Service('')

# Start the browser
driver = webdriver.Chrome(service=service)

# MySQL connection details
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="flights"
)

# List of destination airport codes
cities = [
    "ALC", "BCN", "IBZ", "MAD", "SVQ", "VLC", "AGP", "CGN",
    "OPO", "LIS", "FAO", "KRK", "EIN", "BLQ", "NAP", "MRS",
    "PMO", "RMI", "FCO", "DUB", "EDI", "STN", "MAN", "BVA"
]

# Get today's date and calculate the next days
start_date = datetime.now() #+ timedelta(days=1)
num_days = 3


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
                departure_time = card.find_element(By.CSS_SELECTOR,
                                                   '[data-ref="flight-segment.departure"] .flight-info__hour').text
                arrival_time = card.find_element(By.CSS_SELECTOR,
                                                 '[data-ref="flight-segment.arrival"] .flight-info__hour').text

                origin_city = card.find_element(By.CSS_SELECTOR,
                                                '[data-ref="flight-segment.departure"] .flight-info__city').text
                destination_city = card.find_element(By.CSS_SELECTOR,
                                                     '[data-ref="flight-segment.arrival"] .flight-info__city').text
                flight_number = card.find_element(By.CSS_SELECTOR, '.card-flight-num__content').text

                origin_airport = \
                    card.find_element(By.CSS_SELECTOR, '[data-ref^="origin-airport__"]').get_attribute(
                        'data-ref').split(
                        "__")[1]
                destination_airport = \
                    card.find_element(By.CSS_SELECTOR, '[data-ref^="destination-airport__"]').get_attribute(
                        'data-ref').split("__")[1]

                sold_out = card.find_elements(By.CSS_SELECTOR, 'flights-lazy-sold-out-flight-card')
                if sold_out:
                    price = 'sold out'
                else:
                    price = card.find_element(By.CSS_SELECTOR, '.flight-card-summary__new-value').text

                flight_data.append(
                    [flight_number, origin_city, origin_airport, destination_city, destination_airport,
                     date_out, departure_time, arrival_time, price]
                )

            except Exception as e:
                print(f"Error extracting flight details: {e}")

    else:
        print(f"No flight cards found for {origin} to {destination} on {date_out}.")

    return flight_data


# Function to create the table if it doesn't exist
def create_table_if_not_exists(connection):
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS flights (
        id INT AUTO_INCREMENT PRIMARY KEY,
        flight_number VARCHAR(10),
        origin_city VARCHAR(100),
        origin_airport VARCHAR(10),
        destination_city VARCHAR(100),
        destination_airport VARCHAR(10),
        departure_date DATE,
        departure_time TIME,
        arrival_time TIME,
        price VARCHAR(64)
    );
    """

    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()


# Function to insert flight data into the database
def insert_flight_data(connection, flight_data):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO flights (flight_number, origin_city, origin_airport, destination_city, 
                         destination_airport, departure_date, departure_time, arrival_time, price)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, flight_data)
    connection.commit()
    cursor.close()


#run the create table function
create_table_if_not_exists(connection)

# Loop over each city as destination and scrape flights for the next 7 days
origin = "VIE"
for destination in cities:
    for i in range(num_days):
        # Calculate the date for the specific day
        date_out = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

        # Scrape the flight data for the route and date
        flights = scrape_flights(origin, destination, date_out)

        if flights:
            insert_flight_data(connection, flights)

# Loop over each city as the origin and scrape flights for the next 7 days with Vienna as the destination
destination = "VIE"
for origin in cities:
    for i in range(num_days):
        # Calculate the date for the specific day
        date_out = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

        # Scrape the flight data for the reverse route and date
        flights = scrape_flights(origin, destination, date_out)

        if flights:
            insert_flight_data(connection, flights)

# Close the browser after scraping is complete
driver.quit()
connection.close()

print(f"Flight data has been saved to the MySQL database.")
