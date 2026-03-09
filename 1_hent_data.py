import paramiko
import os
import re

from config import HOST, PORT, USERNAME, PASSWORD, VALG_PATH

transport = paramiko.Transport((HOST, PORT))
transport.connect(username=USERNAME, password=PASSWORD)
sftp = paramiko.SFTPClient.from_transport(transport)

# go into the data folder
sftp.chdir(VALG_PATH)

# download the json files in the data/raw folder
for filename in sftp.listdir():
    if re.match(r".*\.json", filename):
        sftp.get(filename, os.path.join("data/raw", filename))


# take all the files in data raw and combine them into one csv file in data/processed
    