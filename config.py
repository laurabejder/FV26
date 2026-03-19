# SFTP login information
HOST = "data.valg.dk"
PORT = 22
USERNAME = "Valg"
PASSWORD = "Valg"

# remove "verification" later when the actual data endpoints are ready
REMOTE_PATH = "/data/folketingsvalg-135-24-03-2026/"
RESULTATER_PATH = "resultater/"
KANDIDATER_PATH = "kandidater/" 

FROM_PATH = "data/raw/"
TO_PATH = "data/struktureret/"
FOLDERS = ["valgresultater"] # Folders to download. mangler "mandatfordeling"

PARTIER_INFO = "data/partier.json"