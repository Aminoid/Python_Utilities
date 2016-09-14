#!/usr/bin/python

import os, sys, argparse, re, subprocess
import os.path, socket
import time
import threading
import urllib, urllib2
from bs4 import BeautifulSoup
from googleapiclient.discovery import build


class final_links(object):
	def __init__(self, link, string):
		self.link = link
		self.string= string

def print_error_message(code):
	print "\n"
	if code == 1:
		print "Sorry!!!! Couldn't connect to google."
	elif code == 2:
		print "Sorry!!!! Couldn't get search results from google."
	elif code == 3:
		print "Sorry!!!! Couldn't collect links to download."
	elif code == 4:
		print "No links available to download. Aborting!!!!"
	elif code == 5:
		print "Sorry!!!! No episode uploaded till past week."
	else:
		print "Sorry!!!! Something bad happened."
	print "Try:- \n"\
	      "1. Run this script again.\n"\
	      "2. Check your Internet Connection.\n"\
	      "3. Check the Name of Series/Movie, Season and Episode(s) if they exist.\n"\
	      "4. Search for the episodes individually with season.\n"\
	      "4. Movies or Episode(s) may not have been uploaded yet. Try again in like an hour or so.\n"\
	      "5. Contact the dumbass author. He must have screwed something up.\n"
	sys.exit(1)

def ping_test(url):
	try:
		urllib2.urlopen(url, timeout = 2)
		return True
	except (urllib2.URLError, socket.timeout) as e:
		return False

class progress_thread (threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.is_running = True
	def run(self):
		while self.is_running:
			sys.stdout.write("...")
			sys.stdout.flush()
			time.sleep(1)			
	def stop(self):
		print "[Done]"
		self.is_running = False

def reporthook(blocks_read, block_size, total_size):
	progress = int(blocks_read * block_size)
	percent_done = progress * 100. / total_size
	done = int(progress * 50 / total_size)
	if progress < total_size:
		sys.stdout.write("[%s%s][%d/%d MB (%3.2f%%)] \r" %
				('=' * done, ' ' * (50 - done),
				 int(progress/(1024**2)), 
				 int(total_size/(1024**2)), percent_done))
	sys.stdout.flush()
	return

def custom_web_search(name, season):
	date = ""
	if season == '-1':
		date = 'w1'
	if season == None or season == "-1":
		query = name
	else:
	 	if len(season) <= 1:
			season = '0' + season
	 	query = "%s S%s" %(name, season)
	sys.stdout.write("Searching for your query")
	sys.stdout.flush()
	thread = progress_thread()
	thread.start()
	try:
		service = build("customsearch", "v1", 
		       		developerKey="AIzaSyAtUymRvbKnMj2X1uFSqHscjj-UIkJJHbU")
		res = service.cse().list(
	      		q = query,
	          	cx = '010582316405321459485:s1wlxxmjmh8',
			dateRestrict = date
	    	).execute()
	except:
		thread.stop()
		print_error_message(1)
	thread.stop()
	if res["searchInformation"]["totalResults"] == '0':
		if season == "-1":
			print_error_message(5)
		print_error_message(2)
	sys.stdout.write ("Found %s links. Selecting the best one"
			  % (res['searchInformation']['totalResults']))
	thread3 = progress_thread()
	thread3.start()
	for item in res['items']:
		if ping_test(item['link']):
			thread3.stop()
			return item['link']
	thread3.stop()
	print_error_message(2)

def get_download_links(url, name, episode_list):
	final_array = []
	thread2 = progress_thread()
	sys.stdout.write("Collecting links")
	sys.stdout.flush()
	try:
		thread2.start()
		page = urllib.urlopen(url)
		soup = BeautifulSoup(page, "html.parser")
		if episode_list != None:
			all_links = soup.find_all("a", href=re.compile('mkv'))
	
			for ep in episode_list:
				ep = str(ep)
				if len(ep) == 1:
					ep = '0' + ep
				check_string = "E" + ep
				for link in all_links:
					tmp = str(link)
					if tmp.find(check_string) > 0:
						tmp_name = prettify_name(str(link.string))
						final_array.append(final_links(url + link['href'], tmp_name))
						break
		elif name == None:
			all_links = soup.find_all('a')
			for link in all_links:
				final_array.append(final_links(url + link['href'],
						   link.string))	
		
		else:
			i = 1
			small_array = []
			all_mkv = soup.find_all('a', href=re.compile(name.replace(" ", ".")))
			all_mp4 = soup.find_all('a', href=re.compile(name))
			thread2.stop()
			if (len(all_mkv) + len(all_mp4)) <= 0:
				raise Exception
			print "Found following files for %s" %(name)
			for mkv in all_mkv:
				print "%d. %s" %(i, mkv['href'])
				i += 1
				small_array.append(final_links(url + mkv['href'], mkv['href']))
			for mp4 in all_mp4:
				print "%d. %s" %(i, mp4['href'])
				i += 1
				small_array.append(final_links(url + mp4['href'], mp4['href']))
			while True:
				sys.stdout.write("Select one (Enter a number): ")
				choice = int(raw_input())
				if choice in range(1, len(small_array) + 1):
					final_array.append(small_array[choice - 1])
					break
				else:
					print "Invalid Choice"
		        return final_array			
			
	except Exception as e:
		thread2.stop()
		print e
		print_error_message(3)
	thread2.stop()
	return final_array

def download_single_file(url, name):
	print ("Downloading %s " % (name))
	if os.path.isfile(name):
		print "[File already exists....skipping]"
	else:
		filename, msg = urllib.urlretrieve(url, name, reporthook=reporthook) 
		print ""

def download_files(links_data):
	if len(links_data) <= 0:
		print_error_message(4)
	for data in links_data:
		download_single_file(data.link, data.string)
	print "Download Complete!!!!!"
	sys.exit(1)

def prettify_name(name):
	i = name.find("(")
	if i > 0:
		return (name[:i] + ".mkv")
	else:
		return name

def prettify_url(url):
	if url[-1] != "/":
		index = url.rfind("/")
		url = url[:(index+1)]
	return url

def download_url(url, name, episode_list):
	url = prettify_url(url)
	links_data = get_download_links(url, name, episode_list)
	download_files(links_data)

def download_latest_url(url):
	url = prettify_url(url)
	page = urllib.urlopen(url)
	soup = BeautifulSoup(page, "html.parser")
	all_links = soup.find_all("a", href=re.compile("mkv"))
	tmp_name = prettify_name(all_links[-1].string)
	sys.stdout.write("This will download %s." % (tmp_name))
	while True:
		sys.stdout.write("Continue? [y/n]")
		choice = raw_input().lower()
		if choice == 'y':
			download_single_file(all_links[-1]['href'],
					     all_links[-1].string)
		elif choice == 'n':
			sys.exit(1)
		else:
			sys.stdout.write("Invalid Choice")
			

def main_downloader(name, season, episode_list):
	if season != None:
		season = str(season)
	if episode_list == None and season != '-1':
		if season != None:
			season = str(season)
			ask_str = "This will download the entire Season %s of %s." % (season, name) 
		else:
			ask_str = "Make sure you have exact name of the movie (Check IMDB)."
		print ask_str
		while True:
			sys.stdout.write ("Are you sure you want to continue? [y/n] ")
			choice = raw_input().lower()
			if choice == 'y':
				if season != None:
					episode_list = list(range(1, 41))
				break
			elif choice == 'n':
				sys.exit(1)
			else:
				print "Invalid Choice"

	url = custom_web_search(name, season)
	if season == "-1":
		download_latest_url(url)
	download_url(url, name, episode_list)

def url_downloader(url):
	print "This will download all the files present in this url"
	download_url(url, None, None)

if __name__ == "__main__":
	parser = argparse.ArgumentParser("Automating the Download Process")
	subparsers = parser.add_subparsers(help="Options to download.")
	
	series_subparser = subparsers.add_parser("series", help="Download Series")
	series_subparser.add_argument("-n", "--name", required="true", nargs="*", 
				      help="Exact name of the series on IMDB (Required)")
	series_subparser.add_argument("--latest", action='store_true', 
				      help="Download the latest episode of the series")
	series_subparser.add_argument("-s", "--season", type=int, nargs=1, 
				      help="Season to download")
	series_subparser.add_argument("-e", "--episode", help="Episode(s) (Optional)", type=int, nargs="*")
	series_subparser.add_argument("-d", "--directory", help="Directory to download into (Optional)")
	
	movies_subparser = subparsers.add_parser("movies", help="Download Movies")
	movies_subparser.add_argument("-n", "--name", required="true", nargs="*", 
				      help="Exact name of the movie on IMDB (Required)")
	movies_subparser.add_argument("-d", "--directory", help="Directory to download into (Optional)")

	url_subparser = subparsers.add_parser("url", help="Download all links in the url")
	url_subparser.add_argument("link", help="URL to download all the links from")
	

	args = parser.parse_args()
	if hasattr(args, "link"):
		url_downloader(args.link)

	if args.directory != None:
		try:
			os.stat(args.directory)	
		except: 
			os.makedirs(args.directory)
		os.chdir(args.directory)
	if hasattr(args, "season"):
		if args.latest == False and args.season != None:
			main_downloader(" ".join(args.name), args.season[0], args.episode)
		elif args.latest != False and args.season == None:
			main_downloader(" ".join(args.name), -1, None)
		else:
			print "One and only one out of --season | --latest must be specified."
			sys.exit(1)
	else:
		main_downloader(" ".join(args.name), None, None)


