import os
import subprocess
from datetime import datetime
from time import time

home_path   = "D:\Stuff\Code\git\SB-Stats"

source_path = "D:\Stuff\SponsorBlock\Archive"
output_path = "D:\Stuff\Code\git\SB-Stats\data"

sponsorTimes_source = os.path.join(source_path, "sponsorTimes")
userNames_source    = os.path.join(source_path, "userNames")

last_timecheck = time()

for item in os.walk(sponsorTimes_source):
	dir, folders, files = item
	for sponsorTimes_filename in files:
		if sponsorTimes_filename.endswith("sponsorTimes.csv"):
			datestamp = sponsorTimes_filename.split("_")[0]

			dest_leaderboard_path = os.path.join(output_path, f"leaderboard\{datestamp}_leaderboard.json")
			dest_globals_path     = os.path.join(output_path, f"Global Stats\{datestamp}_global_stats.json")
			
			if not os.path.exists(dest_leaderboard_path):
				current_time = datetime.now()
				timestamp = f"{current_time.hour}:{str(current_time.minute).zfill(2)}:{str(current_time.second).zfill(2)}"
				print(f"{timestamp} - Running on {sponsorTimes_filename}")
				usernames_file = os.path.join(userNames_source, datestamp + "_userNames.csv")
				if os.path.exists(usernames_file):
					sponsorTimes_path = os.path.join(dir, sponsorTimes_filename)
					usernames_path    = os.path.join(dir, usernames_file)

					subprocess.run(["python", "generate_leaderboard.py", sponsorTimes_path, usernames_path], capture_output=True)
					new_leaderboard_path = os.path.join(home_path, "leaderboard.json")
					new_globals_path     = os.path.join(home_path, "global_stats.json")
				
					if os.path.exists(new_leaderboard_path):
						os.rename(new_leaderboard_path, dest_leaderboard_path)
					
					if os.path.exists(new_globals_path):
						os.rename(new_globals_path, dest_globals_path)
						
					print("Time taken : " + str(round(time() - last_timecheck, 1)))
					last_timecheck = time()