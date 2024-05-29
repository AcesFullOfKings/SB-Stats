import platform
import os

current_platform = platform.system()

if current_platform == "Darwin":  # macOS
	home_folder = ""
	archive_path = "download/archive"
elif current_platform == "Linux": # rasbpi or cloud server
	home_folder = "/home/AcesFullOfKings/server/"
	archive_path = "/mnt/WhiteBox/SponsorBlock/download/archive"
elif current_platform == "Windows":
	archive_path = "download\\archive"
	home_folder = "D:\\Stuff\\Code\\git\\SB-Stats"
else:
	raise ValueError(f"Unknown platform: {current_platform}")

data_path   = os.path.join(home_folder, "Data")
server_path = os.path.join(home_folder, "Server")