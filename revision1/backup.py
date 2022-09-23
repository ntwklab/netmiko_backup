from netmiko import ConnectHandler
import time
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import queue
from threading import Thread

def open_csv():
    # Create a dataframe from csv
    df = pd.read_csv('device_list.csv', delimiter=',')
    # Create a list of tuples for Dataframe rows using list comprehension
    csv_data = [tuple(row) for row in df.values]
    print("\n")
    return csv_data


def create_device_list(csv_data):
    i = 0
    device_list = list()
    ip_list = list()
    for device in csv_data:
        ip,hostname,username = csv_data[i]

        # Load the .env file
        load_dotenv()
        # Assign corerct password for username
        if username == "admin":
            user_pass = os.getenv("ADMIN_DEVICE_PASSWORD")
        elif username == "cisco":
            user_pass = os.getenv("CISCO_DEVICE_PASSWORD") 
        else:
            user_pass = os.getenv("TACACS_DEVICE_PASSWORD")

        # Iterating over the list with the devices ip addresses
        cisco_device = {
               "device_type": "cisco_ios",
               "host": ip,
               "username": username,
               "password": user_pass,
               "port": 22,
               "secret": "cisco", #this is the enable password
               "verbose": True
               }
        device_list.append(cisco_device)
        ip_list.append(ip)
        # Add 1 to i for the next device
        i += 1
    return device_list,ip_list


# Create list of IPs
def ip_list(ips_list):
    # Devices Connecting to...
    print("\nThese are the devices that we will be connecting to...")
    for ip in ips_list:
        print(f"IP Address: {ip}")
    print("\n")


def config(device, backup_list, error_ips):

    while True:
        device = q.get()

        try:
            connection = ConnectHandler(**device)

            # Get device hostname & IP
            prompt = connection.find_prompt()
            hostname = prompt[0:-1]
            host_ip = device["host"]

            # Enable Mode Check
            prompt = connection.find_prompt()
            if ">" in prompt:
                connection.enable()

            output = connection.send_command("sh run")

            # Closing the connection
            connection.disconnect()

            now = datetime.now()
            year = now.year
            month = now.month
            day = now.day
            file_name = f"{hostname}_{year}-{month}-{day}_backup.cfg"

            with open(file_name, "w") as f:
                f.write(output)

            backup_dict = {"IP Address":host_ip, 
                            "Hostname":hostname, 
                            "File Name":file_name} 
            backup_list.append(backup_dict)  


        except:
            error = device["host"]
            print(f"There is an error connecting to {error}" )
            print("Continuing...\n")
            error_ips.append(device["host"])
        
        q.task_done()



if __name__ == '__main__':

    startTime = time.time()
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Open CSV
    csv_data = open_csv()

    # Create the device list
    device_list,ips_list = create_device_list(csv_data)
    ip_list(ips_list)

    q = queue.Queue()
    backup_list = []
    error_ips = []
    for thread_no in range(8):
        worker = Thread(target=config, args=(q, backup_list, error_ips, ), daemon=True)
        worker.start()

    for device in device_list:
        q.put(device)

    q.join()


    # Print IPs with errors
    print("\n")
    print("*"*60)
    if error_ips != []:
        for ip in error_ips:
            print(f"Error connecting to {ip}")
            with open ("Backup_Connection_Error_IPs.txt", "a") as f:
                f.write(ip + "\n")

    # Print Backups
    print("\n")
    for device in backup_list:
        print(f"Successfully performed backup on:\t{device['Hostname']}\t{device['IP Address']}\t file: {device['File Name']}")
    print("*"*60)

    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))
