import os
import json
import requests

url = "https://sponsor.ajay.app/database.json?generate=false"
response = requests.get(url)

db_info = response.json()
last_updated = db_info["lastUpdated"]

os.rename("download/sponsorTimes.csv", f"download/sponsorTimes_{last_updated}.csv")
os.rename("download/userNames.csv", f"download/userNames_{last_updated}.csv")

os.system(f"rsync -ztvPLK --no-W --inplace rsync://rsync.sponsor.ajay.app:31111/sponsorblock/sponsorTimes_{last_updated}.csv download")
os.system(f"rsync -ztvPLK --no-W --inplace rsync://rsync.sponsor.ajay.app:31111/sponsorblock/userNames_{last_updated}.csv download")

os.rename(f"download/sponsorTimes_{last_updated}.csv", "download/sponsorTimes.csv")
os.rename(f"download/userNames_{last_updated}.csv", "download/userNames.csv")
os.remove("db.json")