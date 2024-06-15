import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('railway.db') #create database

current_page='Login or Sign Up' #create current page

c=conn.cursor() #execute the connection of database


def  createDB():
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT,password TEXT)')  #create users table
    c.execute('CREATE TABLE IF NOT EXISTS employees(employeeID TEXT,password TEXT, designation TEXT)') #create employees table
    c.execute('CREATE TABLE IF NOT EXISTS trains(trainNO TEXT,trainName TEXT ,departureDate TEXT,startDestination TEXT,endDestination TEXT)') #create trains table

    createDB()


#SEARCH A TRAIN

def searchTrain(trainNO):
    trainQuery=c.execute('SELECT * FROM trains WHERE trainNO=?',(trainNO))
    trainData =trainQuery.fetchone()
    return trainData

#SEARCH A TRAIN BY DESTINATION

def trainDes(startDes,endDes):
    trainQuery=c.execute('SELECT * FROM trains WHERE startDestination=?,endDestination=?',(startDes,endDes))
    trainData =trainQuery.fetchone()
    return trainData

#ADD A TRAIN

def addTrain(trainNO,trainName,departureDate,startDest,endDest):
    c.execute('INSERT INTO trains(trainNO,trainName,departureDate,startDestination,endDestination) values (?,?,?,?,?)',(trainNO,trainName,departureDate,startDest,endDest))
    conn.commit()

#CREATE SEAT TABLE FOR TRAIN

def createSeatTable(trainNO):
    c.execute(f'CREATE TABLE IF NOT EXIST seats{trainNO}'
              f'(seatNO INTEGER PRIMARY KEY)'
              f'seatType TEXT'
              f'booked INTEGER'
              f'passengerName TEXT'
              f'passengerAge INTEGER'
              f'passengerGender TEXT)')
    
    for i in range(1,51):
        val=categorizeSeat(i)
        c.execute(f'''INSERT INTO seats_{trainNO}(seatNO,seatType,booked,passengerName,passengerAge,passengerGender) VALUES(?,?,?,?,?,?);''',(i,val,0,''','''))
        conn.commit()


#ALLOCATE NEXT AVAILABLE SEAT

def allocateNextAvaSeat(trainNO,seatType):
    seatQuery=c.execute(f'SELECT seatNO FROM seats_{trainNO} WHERE booked=0 and seatType=?'
                        f'ORDER BY seatNO asc',(seatType))
    result = seatQuery.fetchall()

    if result:
        return[0]

#CATERGORIZE SEAT IN TRAIN

def categorizeSeat(seatNO):
    if(seatNO % 10) in [0,4,5,9]:
        return 'Windows Seat'
    elif(seatNO % 10) in [2,3,6,7]:
        return 'Aisle Seat'
    else:
        return 'Middle Seat'
    
#VIEW SEATS 

def viewSeat(trainNO):
    seatQuery=c.execute(f'''SELECT 'Number: '|| seatNO, '\n Type:'||seatType,'\n
                       Name:'||passengerName, '\n Age:'|| passengerAge, '\n Gender:'||passengerGender as Details , booked FROM seats_{trainNO} ORDER BY seatNO asc''')
    
    result   =seatQuery.fetchall()

    if result:
        st.dataframe(data=result)

#BOOK TICKETS

def bookTickets(trainNO,passengerName,passengerAge,passengerGender,seatType):
    trainQuery=c.execute('SELECT * FROM trains WHERE trainNO=?',(trainNO))
    trainData =trainQuery.fetchone()

    if trainData:
        seatNo=allocateNextAvaSeat(trainNO,seatType)

        if seatNo:
            c.execute(f'UPDATE seats_{trainNO} SET booked=1, seatType=?, passengerName=?, passengerAge=?, passengerGender=?'
                      f'WHERE seatNO=?',(seatType,passengerName,passengerAge,passengerGender,seatNo[0]))
            
            conn.commit()

            st.success(f'Seat booked succesfully !')

#CANCEL TICKETS

def cancelTickets(trainNO,seatNO):
    trainQuery=c.execute('SELECT * FROM train WHERE trainNO=?',(trainNO))
    trainData =trainQuery.fetchone()

    if trainData:
        c.execute(f'''UPDATE seats_{trainNO} SET booked=0, passengerName='',passengerAge='',passengerGender='' WHERE seatNO=?''',(seatNO))

        conn.commit()

        st.success(f'Seat canceled succesfully !')


#DELETE A TRAIN

def deleteTrain(trainNO,departureDate):
    trainQuery=c.execute('SELECT * FROM trains WHERE trainNO=?',(trainNO))
    trainData =trainQuery.fetchone()

    if trainData:
        c.execute('DELETE FROM trains WHERE trainNO=? AND departuureDate=?',(trainNO,departureDate))

        conn.commit()

        st.success('Train is deleted succesfully !')

#APPLY ALL THE FUNCTION

def trainFnc():

    st.title("Train Administrator")
    fnc = st.selectbox("select train",['Add Train','View Train','Search Train','Delete Train','Book Tickets','Cancel Ticket', 'View Seats'])

    if fnc=='add train':
        st.header('Add new train')
        with st.form(key='new_train_details'):
            trainNO=st.text_input('train number')
            trainName=st.text_input('train name')
            departureDate=st.text_input('date')
            startDest=st.text_input('start destination')
            endDest=st.text_input('end destination')
            submitted=st.form_submit_button('Add Train')

            if submitted and trainName !='' and trainNO!='' and startDest!='' and endDest!='':
                addTrain(trainNO,trainName,departureDate,startDest,endDest)
                st.success('Train added succesfully !')

    elif fnc=='view train':
            st.title('View trains')
            trainQuery=c.execute('SELECT * FROM trains')
            trains=trainQuery.fetchall()

    elif fnc=='book tickets':
            st.title('Book train tickets')
            trainNO=st.text_input('Train Number')
            seatType=st.selectbox('Seat Type',['Window','Middle','Aisle'],index=0)
            passengerName=st.text_input('Passenger Name')
            passengerAge =st.number_input('Passenger Age',min_value=1)
            passengerGender=st.selectbox('Gender',['Male','Female'],index=0)

            if st.button('book ticket'):
                if trainNO and passengerName and passengerAge and passengerGender:
                    bookTickets(trainNO,passengerName,passengerAge,passengerGender,seatType)

    elif fnc=='cancel ticket':
        st.title('Cancel Ticket')
        trainNO=st.text_input('Train Number')
        seatNo =st.number_input('Seat Number',min_value=1)
        if st.button('Cancel Ticket'):
            if trainNO and seatNo:
                cancelTickets(trainNO,seatNo)

    elif fnc=='view seats':
        st.title('View Seats')
        trainNO=st.text_input('Train Number')
        if st.button('submit'):
            if trainNO:
                viewSeat(trainNO)

    elif fnc=='delete train':
        st.title('Delete Train')
        trainNo=st.text_input('Train Number')
        departureDate=st.date_input('Select Date')
        if st.button("Delete Train"):
            if  trainNO:
                c.execute(f'DROP TABLE IF EXISTS seats_{trainNO}')
                deleteTrain(trainNO,departureDate)







