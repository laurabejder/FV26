import paramiko
import os
import re

from config import HOST, PORT, USERNAME, PASSWORD

transport = paramiko.Transport((HOST, PORT))
transport.connect(username=USERNAME, password=PASSWORD)
sftp = paramiko.SFTPClient.from_transport(transport)

# go into the directory data
sftp.chdir("data/kommunalvalg-134-18-11-2025/verifikation/valgresultater")

# print all the files in the directory
files = sftp.listdir()
print("Files in data directory:", files)

# list all files in the remote directory

