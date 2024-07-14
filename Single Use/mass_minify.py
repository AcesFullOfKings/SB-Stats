"""
sponsortimes.csv: videoID,startTime,endTime,votes,locked,incorrectVotes,UUID,userID,timeSubmitted,
				  views,category,actionType,service,videoDuration,hidden,reputation,shadowHidden,
				  hashedVideoID,userAgent,description
				  16.7M rows

usernames.csv:    userID,userName,locked
				  315k rows
"""

import os
import csv
import base64

from time import time
from postprocess import csv_to_sql, log
from config      import sponsorTimes_sql_archive_path

archive_folder = "/mnt/WhiteBox/SponsorBlock/Archive/SponsorTimes"
done_folder = "/mnt/WhiteBox/SponsorBlock/Archive/converted_sponsorTimes"

sponsorblock_epoch = 1564088876 # the timestamp of the first submitted segment. All segs are after this time.

try:
	os.mkdir(done_folder)
except FileExistsError:
	pass

with open("all_personabots.txt", "r") as f:
	personabots = set(f.read().split("\n"))

def minify_sponsorTimes(filename, mini_filepath):
	log(f"Processing {filename}..")
		
	# set up segs reader:
	sponsorTimes_filepath = os.path.join(archive_folder, filename)
	sponsortimes = open(sponsorTimes_filepath, "r", encoding="utf-8")
	
	first_row = sponsortimes.readline() # discard this so it's not processed in the loop below
	del first_row

	sponsortimes_field_names = ["videoID","startTime","endTime","votes","locked","incorrectVotes","UUID","userID","timeSubmitted","views","category","actionType","service","videoDuration","hidden","reputation","shadowHidden","hashedVideoID","userAgent","description"]
	segment_reader = csv.DictReader(sponsortimes, fieldnames=sponsortimes_field_names)

	# set up mini sponsorTimes writer:
	mini_file = open(mini_filepath, "w")
	mini_writer = csv.writer(mini_file)
	mini_writer.writerow(["UUID", "userID", "videoID", "startTime", "endTime", "views", "categoryType", "votes", "hiddenShadowHiddenLocked","timeSubmitted"])

	mini_categories = {"sponsor":"s", "selfpromo":"u", "intro":"i", "outro":"o", 
				   "preview":"p", "interaction":"r", "poi_highlight":"h", 
				   "exclusive_access":"e", "filler":"f", "chapter":"c",
				   "music_offtopic":"n"}
	mini_types = {"full":"f", "skip":"s", "mute":"m", "poi":"p", "chapter":"c"}

	line_num = 0

	for segment in segment_reader:
		# Stuff for stats:
		votes         = int(segment["votes"])
		hidden        = int(segment["hidden"])
		shadowHidden  = int(segment["shadowHidden"])
		endTime       = float(segment["endTime"])
		startTime     = float(segment["startTime"])
		views         = int(segment["views"])
		userID        = segment["userID"]
		actionType    = segment["actionType"] # can be skip, mute, full, poi, or chapter
		timeSubmitted = int(int(segment["timeSubmitted"])/1000) #the db encodes this in milliseconds, but I want it in seconds.

		if userID not in personabots:
			# Extra stuff to keep for mini file:

			UUID = segment["UUID"]

			try:
				mini_UUID = int(UUID.replace("-", ""), 16) # convert from base-16 str (hex) to an int
				mini_userID = int(userID.replace("-", ""), 16)
			except ValueError:
				pass
				#print("Ignoring bad hex in row: "+ str(segment))

			else: # runs if the try: block doesn't raise an exception
				videoID  = segment["videoID"]
				category = segment["category"] # sponsor, filler, selfpromo etc
				
				locked   = int(segment["locked"])
				mini_starttime = round(startTime, 2)
				mini_endtime = round(endTime, 2)

				mini_category = mini_categories.get(category, "?")
				#if mini_category == "?": print(f"unknown category on seg {UUID}: {category}")
				mini_type = mini_types.get(actionType, "?")
				#if mini_type == "?": print(f"unknown actionType: {actionType}")

				mini_HSL = 4*hidden + 2*shadowHidden + locked # packs the three bools into a single binary number 000-111 (saved as 0-7).
				mini_timeSubmitted = timeSubmitted - sponsorblock_epoch # make all timestamps relative to the first segment. Saves digits!

				mini_writer.writerow([mini_UUID, mini_userID, videoID, mini_starttime, mini_endtime, views, mini_category+mini_type, votes, mini_HSL, mini_timeSubmitted])
		line_num += 1
		if not line_num % 1_000_000:
			log(f"Processing line {line_num}..")

	sponsortimes.close()
	mini_file.close()
	

for sponsorTimes_filename in os.listdir(archive_folder):
	if sponsorTimes_filename.endswith("sponsorTimes.csv"):
		try:
			sql_filepath = os.path.join(sponsorTimes_sql_archive_path, sponsorTimes_filename.replace(".csv", "_mini.sqlite3"))
			if not os.path.exists(sql_filepath):
				file_start_time = time()
				minify_sponsorTimes(sponsorTimes_filename, "sponsorTimes_mini.csv")
				csv_to_sql("sponsorTimes_mini.csv", sql_filepath)

				source = os.path.join(archive_folder, sponsorTimes_filename)
				dest = os.path.join(done_folder, sponsorTimes_filename)

				os.rename(source, dest) # move minified file to _converted folder
				file_end_time = time()
				secs = file_end_time - file_start_time
				mins = int(secs//60)
				secs = int(secs%60)
				log(f"Time taken: {mins}m {secs}s")
			else:
				log(f"Skipping existing mini file for {sponsorTimes_filename}..")
		except Exception as ex:
			log(f"Exception in {sponsorTimes_filename}: {ex}")
		finally:
			try:
				os.remove("sponsorTimes_mini.csv")
			except Exception as ex:
				log("Unable to remove sponsorTimes_mini.csv")