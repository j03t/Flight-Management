import sqlite3
from prettytable import PrettyTable
from datetime import datetime

conn = sqlite3.connect('flight_management')

def get_all_flights():
  cursor = conn.execute("SELECT F.ID, F.STATUS, F.SCHEDULED_DEPARTURE, F.EXPECTED_ARRIVAL, \
  P.FIRST_NAME||' '||P.LAST_NAME, D1.FULL_NAME, D2.FULL_NAME, ACTUAL_DEPARTURE, ACTUAL_ARRIVAL FROM FLIGHTS AS F LEFT JOIN PILOTS AS P ON F.PILOT_ID = P.ID\
  LEFT JOIN DESTINATIONS AS D1 ON D1.SHORT_NAME = F.FROM_DESTINATION LEFT JOIN DESTINATIONS AS D2 ON D2.SHORT_NAME = F.TO_DESTINATION")
  t = PrettyTable(['FLIGHT_ID', 'FLIGHT_STATUS', "SCHEDULED_DEPARTURE", "EXPECTED_ARRIVAL", "PILOT", "FROM_DESTINATION", "TO_DESTINATION", "ACTUAL_DEPARTURE", "ACTUAL_ARRIVAL"])
  for row in cursor:
     t.add_row(row)
  print(t)

date_format = "%d/%m/%Y"

def flight_search():
  print("Leave blank if not required")
  status = input("Status: ")
  date = input("Date of departure: ")
  if date:
    print("FORMAT DATE")
    try:
      date = datetime.strptime(date, date_format).isoformat()
    except:
      print("Invalid date supplied, please use format: dd/mm/YYYY")
  pilot_id = input("Pilot ID: ")
  from_dest = input("Departing from: ")
  to_dest = input("Flying to: ")
  cursor = conn.execute(
    "SELECT * FROM FLIGHTS \
    WHERE STATUS = COALESCE(NULLIF(?,''), STATUS) \
      AND DATE(SCHEDULED_DEPARTURE) = date(COALESCE(NULLIF(?,''), SCHEDULED_DEPARTURE)) \
        AND PILOT_ID = COALESCE(NULLIF(?,''), PILOT_ID) \
          AND FROM_DESTINATION = COALESCE(NULLIF(?,''), FROM_DESTINATION) \
            AND TO_DESTINATION = COALESCE(NULLIF(?,''), TO_DESTINATION)", (status,date, pilot_id, from_dest, to_dest))
  for row in cursor:
    print(row)

def get_destination(prompt):
  dest = input(prompt)
  cursor = conn.execute("SELECT * FROM DESTINATIONS WHERE SHORT_NAME=?", (dest,))
  row = cursor.fetchone()
  if row:
    return row[0]
  else:
    cursor = conn.execute("SELECT * FROM DESTINATIONS")
    print(dest, " is not a valid short name, please choose from the following valid options:")
    t = PrettyTable(["SHORT NAME","FULL NAME"])
    for row in cursor.fetchall():
      t.add_row(row)
    print(t)
    return get_destination(prompt)

date_time_format = "%H:%M %d/%m/%Y"

def get_date_time(prompt):
  input_date = input(prompt)
  try:
    return datetime.strptime(input_date, date_time_format).isoformat()
  except:
    print("Invalid date supplied, please use format: HH:MM dd/mm/YYYY")
    return get_date_time(prompt)


def create_flight():
  from_destination = get_destination("Leaving From: ")
  to_destination = get_destination("Going to: ")
  scheduled_departure = get_date_time("Scheduled departure time (UTC): ")
  expected_arrival = get_date_time("Expected arrival time (UTC): ")
  conn.execute("INSERT INTO FLIGHTS (STATUS, SCHEDULED_DEPARTURE, EXPECTED_ARRIVAL, FROM_DESTINATION, TO_DESTINATION) VALUES ('Scheduled', ?, ?, ?, ?)", 
               (scheduled_departure, expected_arrival, from_destination, to_destination))
  conn.commit()
  print("Flight Scheduled")

def assign_pilot():
  flight_ids = get_flights_without_pilot()
  if flight_ids:
    flight_id = get_valid_flight_id(flight_ids)
    pilot_ids = get_available_pilots(flight_id)
    if pilot_ids:
      pilot_id = get_valid_pilot_id(pilot_ids)
      conn.execute("UPDATE FLIGHTS SET PILOT_ID = ? WHERE ID = ?", (pilot_id, flight_id))
      conn.commit()
      print("Pilot: ",pilot_id, " assigned to flight: ", flight_id)
    else:
      print("No available pilots\n")
  else:
    print("No flights require pilots\n")
    
def get_flights_without_pilot():
  cursor = conn.execute("SELECT F.ID, F.STATUS, F.SCHEDULED_DEPARTURE, F.EXPECTED_ARRIVAL, D1.FULL_NAME, D2.FULL_NAME, ACTUAL_DEPARTURE, ACTUAL_ARRIVAL \
                        FROM FLIGHTS AS F LEFT JOIN DESTINATIONS AS D1 ON D1.SHORT_NAME = F.FROM_DESTINATION LEFT JOIN DESTINATIONS AS D2 ON D2.SHORT_NAME = F.TO_DESTINATION \
                        WHERE PILOT_ID IS NULL")
  t = PrettyTable(['FLIGHT_ID', 'FLIGHT_STATUS', "SCHEDULED_DEPARTURE", "EXPECTED_ARRIVAL", "FROM_DESTINATION", "TO_DESTINATION", "ACTUAL_DEPARTURE", "ACTUAL_ARRIVAL"])
  flight_ids = []
  for row in cursor:
     t.add_row(row)
     flight_ids.append(str(row[0]))
  if flight_ids:
    print("The following flights have no pilot assigned: ")
    print(t)
  return flight_ids

def get_valid_flight_id(flight_ids):
  flight_id = input("Please enter flight ID: ")
  if flight_id in set(flight_ids):
    return flight_id
  else:
    print("Choose from the values: ", flight_ids)
    return get_valid_flight_id(flight_ids)

def get_available_pilots(flight_id):
  cursor = conn.execute("WITH F1 AS (SELECT DATE(SCHEDULED_DEPARTURE, \"-1 DAY\") MIN, DATE(EXPECTED_ARRIVAL, \"+1 DAY\") MAX FROM FLIGHTS WHERE ID = ?) SELECT ID, FIRST_NAME||' '||LAST_NAME FROM PILOTS WHERE ID NOT IN (SELECT COALESCE(PILOT_ID,0) FROM FLIGHTS WHERE SCHEDULED_DEPARTURE BETWEEN (SELECT MIN FROM F1) AND (SELECT MAX FROM F1))", (flight_id))
  pilot_ids = []
  t = PrettyTable(["PILOT ID", "NAME"])
  for row in cursor:
    pilot_ids.append(str(row[0]))
    t.add_row(row)
  if pilot_ids:
    print("Following pilots are available:")
    print(t)
  return pilot_ids

def get_valid_pilot_id(pilot_ids):
  pilot_id = input("Please enter pilot ID: ")
  if pilot_id in set(pilot_ids):
    return pilot_id
  else:
    print("Choose from the values: ", pilot_ids)
    return get_valid_flight_id(pilot_ids)
  
def onboard_pilot():
  first_name = input("First name: ")
  last_name = input("Last name: ")
  flight_hours = input("Flight hours: ")
  conn.execute("INSERT INTO PILOTS(FIRST_NAME, LAST_NAME, FLIGHT_HOURS) VALUES(?,?,?)", (first_name, last_name, flight_hours))
  conn.commit()
  print("Pilot added\n")

def update_flight():
  match input(
"1) Flight Departed\n\
2) Flight arrived\n"):
    case "1":
      departed()
    case "2":
      arrived()
      # arrived()
  
def departed():
  cursor = conn.execute("SELECT F.ID, F.SCHEDULED_DEPARTURE, F.EXPECTED_ARRIVAL, D1.FULL_NAME, D2.FULL_NAME FROM FLIGHTS F LEFT JOIN DESTINATIONS AS D1 ON D1.SHORT_NAME = F.FROM_DESTINATION LEFT JOIN DESTINATIONS AS D2 ON D2.SHORT_NAME = F.TO_DESTINATION WHERE DATE(F.SCHEDULED_DEPARTURE) = DATE('NOW') AND PILOT_ID IS NOT NULL AND F.STATUS IS 'Scheduled'")
  t = PrettyTable(['FLIGHT_ID', "SCHEDULED_DEPARTURE", "EXPECTED_ARRIVAL", "FROM_DESTINATION", "TO_DESTINATION"])
  flight_ids = []
  for row in cursor:
    t.add_row(row)
    flight_ids.append(str(row[0]))
  if flight_ids:
    print("The following flights are scheduled today: ")
    print(t)
    flight_id = get_valid_flight_id(flight_ids)
    conn.execute("UPDATE FLIGHTS SET STATUS = 'Departed', ACTUAL_DEPARTURE = DATETIME('NOW') WHERE ID = ?", flight_id)
    conn.commit()
    print("Flight ", flight_id, " set to departed")
  else:
    print("No flights left to depart today")

def arrived():
  cursor = conn.execute("SELECT F.ID, F.ACTUAL_DEPARTURE, F.EXPECTED_ARRIVAL, D1.FULL_NAME, D2.FULL_NAME FROM FLIGHTS F LEFT JOIN DESTINATIONS AS D1 ON D1.SHORT_NAME = F.FROM_DESTINATION LEFT JOIN DESTINATIONS AS D2 ON D2.SHORT_NAME = F.TO_DESTINATION WHERE F.STATUS IS 'Departed'")
  t = PrettyTable(['FLIGHT_ID', "ACTUAL_DEPARTURE", "EXPECTED_ARRIVAL", "FROM_DESTINATION", "TO_DESTINATION"])
  flight_ids = []
  for row in cursor:
    t.add_row(row)
    flight_ids.append(str(row[0]))
  if flight_ids:
    print("The following flights are yet to arrive: ")
    print(t)
    flight_id = get_valid_flight_id(flight_ids)
    conn.execute("UPDATE FLIGHTS SET STATUS = 'Arrived', ACTUAL_ARRIVAL = DATETIME('NOW') WHERE ID = ?", flight_id)
    # cursor = conn.execute("WITH T1 AS (SELECT ROUND((JULIANDAY(ACTUAL_ARRIVAL) - JULIANDAY(ACTUAL_DEPARTURE)) * 24) AS FLIGHT_HOURS, PILOT_ID  FROM FLIGHTS WHERE ID = ?) UPDATE PILOTS SET FLIGHT_HOURS = FLIGHT_HOURS + T1.FLIGHT_HOURS WHERE ID = T1.PILOT_ID", flight_id)
    conn.execute("UPDATE PILOTS SET FLIGHT_HOURS = FLIGHT_HOURS + (SELECT ROUND((JULIANDAY(ACTUAL_ARRIVAL) - JULIANDAY(ACTUAL_DEPARTURE)) * 24) AS FLIGHT_HOURS  FROM FLIGHTS WHERE ID = ?) WHERE ID = (SELECT PILOT_ID FROM FLIGHTS WHERE ID = ?)", (flight_id, flight_id))
    conn.commit()
    print("Flight ", flight_id, " set to arrived and pilot flight hours updated")
  else:
    print("No flights waiting to arrive")

while True:
  match input(
"1) Get all flights\n\
2) Search for a flight\n\
3) Create a new flight\n\
4) Assign pilot to flight\n\
5) Onboard a pilot\n\
6) Update flight status\
\n"):
    case "1":
      get_all_flights()
    case "2":
      flight_search()
    case "3":
      create_flight()
    case "4":
      assign_pilot()
    case "5":
      onboard_pilot()
    case "6":
      update_flight()
    case _:
      print("Unrecognised input")
  
