import paramiko
import os
import re

from config import HOST, PORT, USERNAME, PASSWORD, REMOTE_PATH, FROM_PATH, FOLDERS

transport = paramiko.Transport((HOST, PORT))
transport.connect(username=USERNAME, password=PASSWORD)
sftp = paramiko.SFTPClient.from_transport(transport)

# go into the data folder
sftp.chdir(REMOTE_PATH)

# Funktioner til download af filer og mapper
def download_files(sftp, remote_dir, local_dir, folder_name):
    files = sftp.listdir(remote_dir+"/"+folder_name)

    for file in files:   # download each file
        new_file = re.sub(r'-\d{12}(?=\.)', '', file)
        remote_file_path = remote_dir + "/" + folder_name + "/" + file
        local_file_path = os.path.join(local_dir, folder_name, new_file)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        try:
            sftp.get(remote_file_path, local_file_path)
        except Exception as e:
            print(f"Failed to download {remote_file_path}: {e}")

def download_folders(folders):
    for folder in folders:
        download_files(sftp, remote_path, local_path, folder)

# Download FV26 data
remote_path = REMOTE_PATH
local_path = FROM_PATH 
folders = FOLDERS
print("Trying to download:", remote_path)
download_folders(folders)
print("Downloaded FV26 data.")