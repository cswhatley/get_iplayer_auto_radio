#!/usr/bin/env python3

###
# get_iplayer Radio Keyword Scraper by Charles Whatley
#
# get_iplayer wrapper script to download any radio shows matching one of a list of keywords
# Add to your crontab to run regularly, history is automatically tracked by get_iplayer
####

import subprocess
import itertools
import datetime

# Open a temporary file to output the show list to - this way we can keep memory usage down and process it with an iterator
# We'll leave this here so there's always a snapshot of the last run in /tmp
with open("/tmp/radio", "w") as radio:
	subprocess.call(["get_iplayer", "--type=radio", "--listformat=<pid>,<name>,<episode>"], stdout=radio)

# Count the number of lines in the show - we'll use this to skip the first and last few lines of the file
# There are lots of ways to do this but this doesn't involve Python iterating over the entire file
lines = int(subprocess.check_output(["wc", "-l", "/tmp/radio"]).strip().split()[0])

# Keep track of the keywords we're looking for - we'll load these from a file in a minute
keywords = []

# Keep track of files that have already been downloaded - this is done by parsing the get_iplayer history file
history = []

# Read in the keywords we're looking for
with open("/home/pi/radio/keywords", "r") as file:
	for keyword in file:
		keywords.append(keyword.strip())

# Try to open the download history if it exists and add all the pids to it
# <pid>|...|||<pid2>|...|||...
try:
	with open("/home/pi/.get_iplayer/download_history", "r") as download_history:
		downloads = download_history.read().strip().split("|||")
		for download in downloads:
			history.append(download.strip().split("|")[0])
except FileNotFoundError as e:
	pass

# Open the file the show list was output to
with open("/tmp/radio", "r") as radio:
	# Ignore the first 6 lines and the last 2 lines - this doesn't always catch invalid lines
	for show in itertools.islice(radio, 6, lines-2):
		show = show.strip()
		# Strip off the Added: tag for new shows
		if "Added: " in show:
			show = show[7:]
		# Generate a timestamp for this operation
		now = "{:%Y/%m/%d %H:%M:%S.%f}".format(datetime.datetime.now())
		try:
			# Extract the pid, name and episode from the show list
			# <pid>,<name>,<episode>
			pid, name, episode, *rest = show.strip().split(",")
			# Check the pid hasn't already been downloaded
			if pid not in history:
				# Iterate over all the keywords we're looking for
				for keyword in keywords:
					# Check if the keyword is in either the name or the episode
					if keyword in name or keyword in episode:
						print("[" + now + "] Downloading (Match: " + keyword + "): " + show)
						try:
							# Download the show, piping stdout and stderr to the return value output, which we'll ignore for now...
							output = subprocess.check_output(["get_iplayer", "--type=radio", "--pid=" + pid, "--modes=best", "--output=/home/pi/radio/downloads"], stderr=subprocess.STDOUT)
							# Add the pid to history for completeness although get_iplayer will update its download_history file
							history.append(pid)
						except subprocess.CalledProcessError as e:
							print("[" + now + "] Error (get_iplayer): " + e.returncode)
						break
					else:
						print("[" + now + "] Skipping (No Match: " + keyword + "): " + show)
			else:
				print("[" + now + "] Skipping (Downloaded): " + show)
		except ValueError as e:
			print("[" + now + "] Skipping (Invalid): " + show)
