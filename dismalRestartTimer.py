import mysql.connector
import datetime
import subprocess
import os
import socket
import time
from configparser import ConfigParser

# Function to read the database configuration
def read_db_config(filename='backendItems/config.ini', section='database'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    return db

# Service to restart
service_name = "dismalOrinGather.service"

# Get the hostname to use in the query
hostname = socket.gethostname()

# Function to check the timestamp
def check_timestamp():
    try:
        # Load the database configuration
        db_config = read_db_config()

        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Use hostname in table name for the query
        query = f"SELECT MAX(time) FROM {db_config['database']}.{hostname}"
        cursor.execute(query)
        last_timestamp = cursor.fetchone()[0]

        # Check if the last timestamp is in UTC and is more than 2 minutes behind
        if last_timestamp:
            now_utc = datetime.datetime.utcnow()
            time_diff = now_utc - last_timestamp
            if time_diff.total_seconds() > 10:  # 2 minutes in seconds
                print("Timestamp is behind by more than 2 minutes. Restarting the service...")
                restart_service()
            else:
                print("Timestamp is within the acceptable range.")
        else:
            print("No timestamp found in the table.")

        # Close the connection
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Error: {e}")

# Function to restart the service
def restart_service():
    try:
        # Restart the service
        subprocess.run(["systemctl", "restart", service_name], check=True)
        print(f"{service_name} restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart service: {e}")

if __name__ == "__main__":
    while True:
        check_timestamp()
        time.sleep(60)  # Wait for 1 minute before the next check