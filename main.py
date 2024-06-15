import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title='Railway Reservation')

# Database connection setup
def get_db_connection():
    try:
        conn = sqlite3.connect('railway.db')
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return None

conn = get_db_connection()
if not conn:
    st.stop()

c = conn.cursor()

# Create the database tables
def create_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            username TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees(
            employeeID TEXT,
            password TEXT,
            designation TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trains(
            trainNO TEXT,
            trainName TEXT,
            departureDate TEXT,
            startDestination TEXT,
            endDestination TEXT
        )
    ''')
    conn.commit()

create_db()

# Search train by number
def search_train(trainNO):
    c.execute('SELECT * FROM trains WHERE trainNO=?', (trainNO,))
    return c.fetchone()

# Search train by destination
def train_des(startDes, endDes):
    c.execute('SELECT * FROM trains WHERE startDestination=? AND endDestination=?', (startDes, endDes))
    return c.fetchone()

# Add a train
def add_train(trainNO, trainName, departureDate, startDest, endDest):
    c.execute('INSERT INTO trains (trainNO, trainName, departureDate, startDestination, endDestination) VALUES (?, ?, ?, ?, ?)',
              (trainNO, trainName, departureDate, startDest, endDest))
    conn.commit()

# Create seat table for a train
def create_seat_table(trainNO):
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS seats_{trainNO}(
            seatNO INTEGER PRIMARY KEY,
            seatType TEXT,
            booked INTEGER,
            passengerName TEXT,
            passengerAge INTEGER,
            passengerGender TEXT
        )
    ''')
    for i in range(1, 51):
        seat_type = categorize_seat(i)
        c.execute(f'''
            INSERT INTO seats_{trainNO}(seatNO, seatType, booked, passengerName, passengerAge, passengerGender) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (i, seat_type, 0, '', 0, ''))
    conn.commit()

# Categorize seat in train
def categorize_seat(seatNO):
    if seatNO % 10 in [0, 4, 5, 9]:
        return 'Window Seat'
    elif seatNO % 10 in [2, 3, 6, 7]:
        return 'Aisle Seat'
    else:
        return 'Middle Seat'

# Allocate next available seat
def allocate_next_available_seat(trainNO, seatType):
    c.execute(f'''
        SELECT seatNO FROM seats_{trainNO} 
        WHERE booked=0 AND seatType=?
        ORDER BY seatNO ASC
    ''', (seatType,))
    return c.fetchone()

# View seats
def view_seat(trainNO):
    c.execute(f'''
        SELECT seatNO AS 'Number', seatType AS 'Type', 
               passengerName AS 'Name', passengerAge AS 'Age', passengerGender AS 'Gender', 
               booked AS 'Booked' 
        FROM seats_{trainNO} 
        ORDER BY seatNO ASC
    ''')
    result = c.fetchall()
    if result:
        st.dataframe(pd.DataFrame(result))

# Book tickets
def book_tickets(trainNO, passengerName, passengerAge, passengerGender, seatType):
    seatNo = allocate_next_available_seat(trainNO, seatType)
    if seatNo:
        c.execute(f'''
            UPDATE seats_{trainNO} 
            SET booked=1, passengerName=?, passengerAge=?, passengerGender=? 
            WHERE seatNO=?
        ''', (passengerName, passengerAge, passengerGender, seatNo[0]))
        conn.commit()
        st.success('Seat booked successfully!')

# Cancel tickets
def cancel_tickets(trainNO, seatNO):
    c.execute(f'''
        UPDATE seats_{trainNO} 
        SET booked=0, passengerName='', passengerAge=0, passengerGender='' 
        WHERE seatNO=?
    ''', (seatNO,))
    conn.commit()
    st.success('Seat canceled successfully!')

# Delete a train
def delete_train(trainNO, departureDate):
    c.execute('SELECT * FROM trains WHERE trainNO=? AND departureDate=?', (trainNO, departureDate))
    if c.fetchone():
        c.execute(f'DROP TABLE IF EXISTS seats_{trainNO}')
        c.execute('DELETE FROM trains WHERE trainNO=? AND departureDate=?', (trainNO, departureDate))
        conn.commit()
        st.success('Train deleted successfully!')

# Main function to handle train operations
def train_fnc():
    st.title("Train Administrator")
    fnc = st.selectbox("Select Operation", ['Add Train', 'View Trains', 'Search Train', 'Delete Train', 'Book Tickets', 'Cancel Ticket', 'View Seats'], index=0)

    if fnc == 'Add Train':
        st.header('Add New Train')
        with st.form(key='new_train_details'):
            trainNO = st.text_input('Train Number')
            trainName = st.text_input('Train Name')
            departureDate = st.text_input('Date')
            startDest = st.text_input('Start Destination')
            endDest = st.text_input('End Destination')
            submitted = st.form_submit_button('Add Train')
            if submitted and trainName and trainNO and startDest and endDest:
                add_train(trainNO, trainName, departureDate, startDest, endDest)
                st.success('Train added successfully!')

    elif fnc == 'View Trains':
        st.header('View Trains')
        c.execute('SELECT * FROM trains')
        trains = c.fetchall()
        if trains:
            st.dataframe(pd.DataFrame(trains))

    elif fnc == 'Search Train':
        st.header('Search Train')
        trainNO = st.text_input('Train Number')
        if st.button('Search'):
            train = search_train(trainNO)
            if train:
                st.write(train)
            else:
                st.error('Train not found')

    elif fnc == 'Book Tickets':
        st.header('Book Train Tickets')
        trainNO = st.text_input('Train Number')
        seatType = st.selectbox('Seat Type', ['Window Seat', 'Middle Seat', 'Aisle Seat'], index=0)
        passengerName = st.text_input('Passenger Name')
        passengerAge = st.number_input('Passenger Age', min_value=1)
        passengerGender = st.selectbox('Gender', ['Male', 'Female'], index=0)
        if st.button('Book Ticket'):
            if trainNO and passengerName and passengerAge and passengerGender:
                book_tickets(trainNO, passengerName, passengerAge, passengerGender, seatType)

    elif fnc == 'Cancel Ticket':
        st.header('Cancel Ticket')
        trainNO = st.text_input('Train Number')
        seatNO = st.number_input('Seat Number', min_value=1)
        if st.button('Cancel Ticket'):
            if trainNO and seatNO:
                cancel_tickets(trainNO, seatNO)

    elif fnc == 'View Seats':
        st.header('View Seats')
        trainNO = st.text_input('Train Number')
        if st.button('View'):
            if trainNO:
                view_seat(trainNO)

    elif fnc == 'Delete Train':
        st.header('Delete Train')
        trainNO = st.text_input('Train Number')
        departureDate = st.text_input('Date')
        if st.button('Delete Train'):
            if trainNO and departureDate:
                delete_train(trainNO, departureDate)

train_fnc()
