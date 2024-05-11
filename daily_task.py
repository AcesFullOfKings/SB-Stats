import os
from time import time, localtime
from sys import argv

force_update = "-force" in argv

start_time = time()

def log(s):
	current_time = localtime()
	month  = str(current_time.tm_mon ).zfill(2)
	day    = str(current_time.tm_mday).zfill(2)
	hour   = str(current_time.tm_hour).zfill(2)
	minute = str(current_time.tm_min ).zfill(2)

	log_time = f"{day}/{month} {hour}:{minute}"
	print(s)
	with open("log.txt", "a") as f:
		f.write(f"{log_time} - {s}\n")

if __name__ == "__main__":
	if force_update:
		log("Force Update is enabled. Database will be downloaded and analysed even if it's out of date.")
	log("Updating Local Files..")
	if force_update:
		r1 = os.system("python3 update_local_files_compressed.py -force")
	else:
		r1 = os.system("python3 update_local_files_compressed.py")
	log(f"update_local_files_compressed result was {r1}")

	if r1 == 0:
		log("Generating Leaderboard..")
		r2 = os.system("python generate_leaderboard.py")
		log(f"generate_leaderboard result was {r2}")

		if r2 == 0:
			log("Updating PythonAnywhere..")
			r3 = os.system("python updatePAfile.py")
			log(f"updatePAfile result was {r3}")
		else:
			log("Failed when running generate_leaderboard.py")
	else:
		log("Failed when running updateLocalFiles.py")

	log(f"Total time taken for daily_task.py: {round(time()-start_time,1)}s")
