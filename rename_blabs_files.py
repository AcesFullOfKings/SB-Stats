import os
from contextlib import suppress

top_directory = "D:\Stuff\SponsorBlock\Archive\decompressed"

tree = os.walk(top_directory)

logfile = open("log.txt", "w")

try:
	for item in tree:
		dir, folders, files = item
		if dir.endswith("latest"):
			date_folder_name = dir.split("\\")[-2]

			try:
				datestamp = date_folder_name.split("_")[0]
	
				for filename in files:
					source      = os.path.join(dir, filename)
					dest_folder = (os.path.join(top_directory, filename)).replace(".csv", "")

					with suppress(FileExistsError):
						os.mkdir(dest_folder)

					dest = os.path.join(dest_folder, f"{datestamp}_{filename}")

					if os.path.exists(dest):
						os.remove(dest)
						print("removed earlier file: " + dest)

					os.rename(source, dest)

					#print(f"renamed {source} to {dest}")
					#input()
			except Exception as ex:
				print(f"Exception in folder {dir}: {ex}")
				input()
finally:
	logfile.close()