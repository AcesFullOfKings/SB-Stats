"""
daily_task.py

	- downloads csv, and converts  sponsorTimes.csv into sponsorTimes_mini.csv
	- generates today's leaderboard data.
	- calls postprocess.py with today's filename as input

postprocess.py

	- converts mini.csv into sql database and stores on the network
	- generates user stats on today's database from data_userIDs.txt
	- sends user stats to pythonAnywhere
	
"""
import os
import sqlite3
import subprocess

from time import localtime
from config import my_auth_token
	
def log(log_text):
	"""
	Takes a string, s, and logs it to a log file on disk with a timestamp. Also prints the string to console.
	"""
	current_time = localtime()
	# year   = str(current_time.tm_year)
	# month  = str(current_time.tm_mon ).zfill(2)
	# day    = str(current_time.tm_mday).zfill(2)
	hour   = str(current_time.tm_hour).zfill(2)
	minute = str(current_time.tm_min ).zfill(2)
	second = str(current_time.tm_sec ).zfill(2)
	
	log_time = f"{hour}:{minute}:{second}"
	log_text = log_text.replace("\n", "").replace("\r", "") # makes sure each log line is only one line

	print(f"{log_time} - {log_text}")
	with open("postprocess_log.txt", "a", encoding="utf-8") as f:
		f.write(log_time + " - " + log_text + "\n")

def csv_to_sql(csv_path, sql_path):
	if os.path.exists(sql_path):
		# prob, instead of skipping, rename it _old and re-process the new version, then delete _old when done
		log(f"Skipping existing sql file: " + sql_path)
		return
	
	assert csv_path.endswith("_mini.csv")

	csv_filename = os.path.basename(csv_path) # get filename from path
	sql_local_filename = os.path.basename(sql_path) # get filename from path

	log(f"converting {csv_filename} to sql.")
	try:
		#log(f"Creating database at: {sql_path}")

		# if you get "error: database is locked" here when trying to access a db on an smb share,
		# make sure the smb share is mounted with the "nobrl" option: https://stackoverflow.com/a/30284290
		conn = sqlite3.connect(sql_local_filename)
		cursor = conn.cursor()
		
		# Create the table schema with the correct headers
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS sponsorTimes (
		UUID INTEGER,
		userID INTEGER,
		videoID TEXT,
		startTime REAL,
		endTime REAL,
		views INTEGER,
		categoryType TEXT,
		votes INTEGER,
		hiddenShadowHiddenLocked INTEGER,
		timeSubmitted INTEGER );""")

		# Create an index on the userID column
		cursor.execute("CREATE INDEX IF NOT EXISTS idx_userID ON sponsorTimes (userID);")
        
		conn.commit()
		conn.close()
		
		log(f"Importing csv..")

		# Use subprocess to call the SQLite CLI and import the CSV
		import_command = f'sqlite3 {sql_local_filename} ".mode csv" ".import {csv_path} sponsorTimes"'

		try:
			subprocess.run(import_command, shell=True, check=True)
		except subprocess.CalledProcessError as e:
			log(f"An error occurred during import: {e}")

		log("Moving file to network..")
		subprocess.run(f"sudo mv {sql_local_filename} {sql_path}", shell=True, check=True)
	except Exception as e:
		print(f"An error occurred: {e}")
	finally:
		if os.path.exists(sql_local_filename):
			log("Deleting local temporary database..")
			os.remove(sql_local_filename) # this should have been moved to the network. in the case of an error, delete the local temporary version
		log(f"Done.")
		log("-------")