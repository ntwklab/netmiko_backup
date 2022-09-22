from netmiko import ConnectHandler
import getpass
import csv
import pandas as pd
from datetime import datetime
import os




def open_csv():
    # Create a dataframe from csv
    df = pd.read_csv('device_list.csv', delimiter=',')
    # Create a list of tuples for Dataframe rows using list comprehension
    csv_data = [tuple(row) for row in df.values]
    print("\n")
    return csv_data

def create_device_list(csv_data, tacacs_pass, admin_pass):
    i = 0
    device_list = list()
    ip_list = list()
    for device in csv_data:
        ip,hostname,username = csv_data[i]

        # Assign corerct password for username
        if username == "admin":
            user_pass = admin_pass
        else:
            user_pass = tacacs_pass

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

def config(device):
    connection = ConnectHandler(**device)


    # Get device hostname & IP
    prompt = connection.find_prompt()
    hostname = prompt[0:-1]
    host_ip = device["host"]
    print(f"Hostname: {hostname}\nIP Address: {host_ip}")

    # Enable Mode Check
    prompt = connection.find_prompt()
    if ">" in prompt:
        print("Entering the enable mode ...")
        connection.enable()


    print("Show Running Config...\n")
    output = connection.send_command("sh run")
    print("Output gathered...")

    # Closing the connection
    print("Closing connection\n")
    connection.disconnect()



    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    file_name = f"{hostname}_{year}-{month}-{day}_backup.cfg"

    with open(file_name, "w") as f:
        f.write(output)

    print(f"Backup cereated: {file_name}")
    print("#" * 30 +"\n")




if __name__ == '__main__':

    basedir = os.path.abspath(os.path.dirname(__file__))


    # Open CSV
    csv_data = open_csv()

    print("Please Enter your TACACS password")
    tacacs_pass = getpass.getpass()
    print("Please Enter admin password")
    admin_pass = getpass.getpass()


    # Create the device list
    # This needs a if statment here to pass in the corret password
    device_list,ips_list = create_device_list(csv_data, tacacs_pass, admin_pass)
    ip_list(ips_list)


    # Try config
    error_ips = []
    for device in device_list:
        try:
            config(device)   
        except:
            error = device["host"]
            print(f"There is an error connecting to {error}" )
            print("Continuing...\n")
            error_ips.append(device["host"])


    # Print IPs with errors
    if error_ips != []:
        for ip in error_ips:
            print(f"Error connecting to {ip}")
            with open ("Backup_Connection_Error_IPs.txt", "a") as f:
                f.write(ip + "\n")
