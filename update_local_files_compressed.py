import os
import subprocess

from config import archive_path
from time import time
from datetime import datetime, timedelta
from contextlib import suppress
from daily_task import log
from sys import argv

force_update = "-force" in argv

if force_update:
	log("update_local_files.py: Force Update is enabled.")

today = datetime.now()

compressed_segs_server_path = "https://sb.minibomba.pro/mirror/sponsorTimes.csv.zst"
compressed_names_server_path = "https://sb.minibomba.pro/mirror/userNames.csv.zst"

compressed_segs_local_path = f"download/sponsorTimes.csv.zst"
compressed_names_local_path = f"download/userNames.csv.zst"

with suppress(Exception):
	os.remove("download/old_sponsorTimes.csv")

with suppress(Exception):
	#move current file to "old"
	os.rename("download/sponsorTimes.csv", "download/old_sponsorTimes.csv")

if not force_update:
	#Check if the file on the server has been updated since last download:
	result = subprocess.run(["curl", "-s", "-I", compressed_segs_server_path], capture_output=True, text=True)
	headers = result.stdout.split('\n')

	server_last_modified = 999_999_999 # if no last_modified is found, assume the file is new and download it
	for header in headers:
		if header.lower().startswith('last-modified'):
			try:
				server_last_modified = int(datetime.strptime(header.split(": ")[1], '%a, %d %b %Y %H:%M:%S %Z').timestamp())
				break
			except ValueError:
				log(f"Couldn't convert last_modified to int when reading file header. Header is: {header}")

	try:
		with open("last_db_update.txt", "r") as f:
			local_last_modified = int(f.read())
	except FileNotFoundError:
		local_last_modified = 0 # always less than the server's modified time

	print(f"{server_last_modified} ; {local_last_modified}")

	proceed = local_last_modified < server_last_modified
else:
	proceed = True 

if proceed:
	log("Curling segs..")
	os.system(f"curl {compressed_segs_server_path} --output {compressed_segs_local_path}")

	log("Curling names..")
	os.system(f"curl {compressed_names_server_path} --output {compressed_names_local_path}")

	log("Decompressing segs..")
	# (requires brew install zstd)
	cmd_segs = f"zstd -d -f {compressed_segs_local_path}" # decompress the file
	os.system(cmd_segs)

	log("Decompressing names..")
	cmd_names = f"zstd -d -f {compressed_names_local_path}" # decompress the file
	os.system(cmd_names)

	log("Cleaning up compressed files..")
	os.remove(compressed_segs_local_path) # remove the compressed files
	os.remove(compressed_names_local_path)

	if (not os.path.isfile("download/old_sponsorTimes.csv")) or ((new_size := os.path.getsize("download/sponsorTimes.csv")) > (old_size := os.path.getsize("download/old_sponsorTimes.csv"))):
		with open("last_db_update.txt", "w") as f:
			f.write(str(round(time())))
			
		with suppress(Exception):
			os.remove("download/old_sponsorTimes.csv")

		segs_filename_uncompressed = "sponsorTimes.csv"
		names_filename_uncompressed = "userNames.csv"

		log("Copying today's database to the archive..")
		today_string = today.strftime("%Y-%m-%d")
		try:
			os.system(f"sudo cp download/{segs_filename_uncompressed} {archive_path}/{today_string}_{segs_filename_uncompressed}")
			os.system(f"sudo cp download/{names_filename_uncompressed} {archive_path}/{today_string}_{names_filename_uncompressed}")
		except OSError as ex:
			log("Could not copy files to archive - " + str(ex))
	else:
		log(f"Downloaded sponsorTimes.csv is SMALLER than the current file. (new_size is {new_size:,}; old_size is {old_size:,}). Ignoring it.")
		os.remove("download/sponsorTimes.csv")

		with suppress(Exception):
			#put the "old" file back as the current file
			os.rename("download/old_sponsorTimes.csv", "download/sponsorTimes.csv")

		#this exception should cause the result value to be nonzero, stopping the rest of the daily_task process.
		log("New file is not bigger than old file. Aborting. Archive skipped.")
		raise RuntimeError

else:
	log(f"Did not download the remote database because it's not newer than the local file. local_last_modified is {local_last_modified}; server_last_modified is {server_last_modified}.")
	raise RuntimeError


