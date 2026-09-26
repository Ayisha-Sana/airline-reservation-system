import mysql.connector
from datetime import datetime
import sys

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="airline_db"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"\u274c Database connection error: {err}")
        sys.exit(1)

def execute_query(query, values=None, fetchone=False, fetchall=False):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        if conn.is_connected():
            conn.commit()
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return True
    except mysql.connector.Error as err:
        print(f"\u274c Database operation failed: {err}")
        if conn and conn.is_connected():
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_input(prompt, type_cast=str):
    while True:
        try:
            user_input = type_cast(input(prompt))
            return user_input
        except ValueError:
            print("\u274c Invalid input. Please enter a valid value.")

def add_flight():
    print("\n--- Add New Flight ---")
    flight_number = get_input("Flight Number: ")
    origin = get_input("Origin: ")
    destination = get_input("Destination: ")
    departure = get_input("Departure Time (YYYY-MM-DD HH:MM:SS): ", lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
    arrival = get_input("Arrival Time (YYYY-MM-DD HH:MM:SS): ", lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
    seats = get_input("Total Seats: ", int)

    query = """
    INSERT INTO flights (flight_number, origin, destination, departure_time, arrival_time, total_seats, available_seats)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (flight_number, origin, destination, departure, arrival, seats, seats)

    if execute_query(query, values):
        print("\u2705 Flight added successfully.\n")
    else:
        print("\u274c Failed to add flight. It might already exist.\n")

def view_flights():
    query = "SELECT flight_id, flight_number, origin, destination, departure_time, arrival_time, available_seats FROM flights"
    flights = execute_query(query, fetchall=True)

    if flights:
        print("\n--- All Flights ---")
        print(f"{'ID':<5} {'Flight No.':<12} {'Origin':<15} {'Destination':<15} {'Departure':<20} {'Arrival':<20} {'Available Seats':<15}")
        print("-" * 110)
        for flight in flights:
            print(f"{flight[0]:<5} {flight[1]:<12} {flight[2]:<15} {flight[3]:<15} {flight[4].strftime('%Y-%m-%d %H:%M:%S'):<20} {flight[5].strftime('%Y-%m-%d %H:%M:%S'):<20} {flight[6]:<15}")
        print("-" * 110)
    else:
        print("\u274c No flights found.\n")

def search_flight():
    print("\n--- Search Flights ---")
    origin = get_input("Enter origin: ")
    destination = get_input("Enter destination: ")

    query = """
    SELECT flight_id, flight_number, departure_time, arrival_time, available_seats
    FROM flights WHERE origin=%s AND destination=%s
    """
    flights = execute_query(query, (origin, destination), fetchall=True)

    if flights:
        print("\n--- Matching Flights ---")
        print(f"{'ID':<5} {'Flight No.':<12} {'Departure':<20} {'Arrival':<20} {'Available Seats':<15}")
        print("-" * 80)
        for flight in flights:
            print(f"{flight[0]:<5} {flight[1]:<12} {flight[2].strftime('%Y-%m-%d %H:%M:%S'):<20} {flight[3].strftime('%Y-%m-%d %H:%M:%S'):<20} {flight[4]:<15}")
        print("-" * 80)
    else:
        print("\u274c No flights found for this route.\n")

def check_availability():
    print("\n--- Check Flight Availability ---")
    flight_id = get_input("Enter Flight ID: ", int)

    query = "SELECT available_seats FROM flights WHERE flight_id=%s"
    result = execute_query(query, (flight_id,), fetchone=True)

    if result:
        print(f"\u2705 Seats available for Flight ID {flight_id}: {result[0]}\n")
    else:
        print("\u274c Flight not found.\n")

def book_ticket():
    print("\n--- Book New Ticket ---")
    name = get_input("Passenger Name: ")
    flight_id = get_input("Flight ID: ", int)
    seats_requested = get_input("Number of seats to book: ", int)

    query_check_seats = "SELECT available_seats FROM flights WHERE flight_id=%s"
    result = execute_query(query_check_seats, (flight_id,), fetchone=True)

    if result and result[0] >= seats_requested:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO bookings (passenger_name, flight_id, seats_booked) VALUES (%s, %s, %s)",
                           (name, flight_id, seats_requested))
            cursor.execute("UPDATE flights SET available_seats = available_seats - %s WHERE flight_id = %s",
                           (seats_requested, flight_id))
            conn.commit()
            print(f"\u2705 Ticket booked for {name} on flight ID {flight_id}.\n")
        except mysql.connector.Error as err:
            print(f"\u274c Booking failed: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    else:
        print("\u274c Not enough seats available or flight not found.\n")

def view_bookings():
    query = """
        SELECT b.booking_id, b.passenger_name, f.flight_number, b.seats_booked, b.booking_time 
        FROM bookings b
        JOIN flights f ON b.flight_id = f.flight_id
    """
    bookings = execute_query(query, fetchall=True)

    if bookings:
        print("\n--- All Bookings ---")
        print(f"{'Booking ID':<12} {'Passenger Name':<20} {'Flight No.':<12} {'Seats':<6} {'Booking Time':<20}")
        print("-" * 75)
        for b in bookings:
            print(f"{b[0]:<12} {b[1]:<20} {b[2]:<12} {b[3]:<6} {b[4].strftime('%Y-%m-%d %H:%M:%S'):<20}")
        print("-" * 75)
    else:
        print("\u274c No bookings found.\n")

def cancel_ticket():
    print("\n--- Cancel Ticket ---")
    booking_id = get_input("Enter Booking ID to cancel: ", int)

    query_get_flight = "SELECT flight_id, seats_booked FROM bookings WHERE booking_id=%s"
    result = execute_query(query_get_flight, (booking_id,), fetchone=True)

    if result:
        flight_id, seats_booked = result
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM bookings WHERE booking_id=%s", (booking_id,))
            cursor.execute("UPDATE flights SET available_seats = available_seats + %s WHERE flight_id=%s",
                           (seats_booked, flight_id))
            conn.commit()
            print(f"\u2705 Booking ID {booking_id} cancelled. Seats returned to flight {flight_id}.\n")
        except mysql.connector.Error as err:
            print(f"\u274c Cancellation failed: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    else:
        print("\u274c Booking not found.\n")

def print_ticket():
    print("\n--- Print Ticket ---")
    booking_id = get_input("Enter Booking ID: ", int)

    query = """
        SELECT b.booking_id, b.passenger_name, f.flight_number, b.seats_booked, b.booking_time
        FROM bookings b
        JOIN flights f ON b.flight_id = f.flight_id
        WHERE b.booking_id=%s
    """
    result = execute_query(query, (booking_id,), fetchone=True)

    if result:
        print("\n--- Ticket Details ---")
        print(f"Booking ID   : {result[0]}")
        print(f"Passenger    : {result[1]}")
        print(f"Flight No.   : {result[2]}")
        print(f"Seats Booked : {result[3]}")
        print(f"Booked On    : {result[4].strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        print("\u274c Booking not found.\n")

def main_menu():
    while True:
        print("\n--- Airline Reservation System ---")
        print("1. Add Flight")
        print("2. View Flights")
        print("3. Search Flights")
        print("4. Check Availability")
        print("5. Book Ticket")
        print("6. View Bookings")
        print("7. Cancel Ticket")
        print("8. Print Ticket")
        print("9. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            add_flight()
        elif choice == "2":
            view_flights()
        elif choice == "3":
            search_flight()
        elif choice == "4":
            check_availability()
        elif choice == "5":
            book_ticket()
        elif choice == "6":
            view_bookings()
        elif choice == "7":
            cancel_ticket()
        elif choice == "8":
            print_ticket()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("\u274c Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu() 
