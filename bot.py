# A reddit bot to give info on a youtube channel when invoked.
# Extracted using youtube's data api.
# Created by /u/JeffJefftyJeffJeff
# Licence: MIT Licence

import praw
import time
import re
import requests
import os
import logging
import json
import stat

commented_path = os.path.join(os.getcwd(),"commented.txt")
apikey_path = os.path.join(os.getcwd(),"apikey.txt")
robots_path = os.path.join(os.getcwd(),"robots.txt")

channel_api_url = 'https://www.googleapis.com/youtube/v3/channels'
search_api_url = 'https://www.googleapis.com/youtube/v3/search'

header = '#**Top videos for channel {}**\n'
video_line = '* [{}](https://youtube.com/watch?v={})\n'
footer = '\n---\n^(Bot created by /u/JeffJefftyJeffJeff | )[^(Source Code)](https://github.com/JJtJJ/YoutubeRedditBot)'

DAY_IN_SECONDS = 86400

def authenticate():
	# Authenticate this bot
	logging.info('Authenticating...')
	reddit = praw.Reddit('YoutubeRedditBot', user_agent = 'web:youtube-reddit-bot:v0.1 (by /u/JeffJefftyJeffJeff)')
	logging.info('Authenticated as {}'.format(reddit.user.me()))
	return reddit


def getYoutubeData(channel_name):
	key = getApiKey()

	params = {'key': key, 'part': 'snippet', 'type': 'channel', 'q': channel_name, 'maxResults': '1'}
	r = requests.get(search_api_url, params=params)
	channel_json = r.json()
	snippet = channel_json["items"][0]["snippet"]
	channel_id = snippet["channelId"]
	channel_name = snippet["title"]

	params = {'key': key, 'channelId': channel_id, 'order': 'viewCount', 'part': 'snippet', 'type': 'video'}
	r = requests.get(search_api_url, params=params)
	list_json = r.json()
	return channel_name, list_json


def parseData(channel_data):
	items = channel_data["items"][:5]
	return items


def getApiKey():
	with open(apikey_path) as file:
		for line in file:
			name, var = line.partition(":")[::2]
			if name == 'key':
				return var


def prettifyItem(item):
	s = video_line.format(item["snippet"]["title"], item["id"]["videoId"])
	return s


def buildComment(channel_name, items):
	s = header.format(channel_name) + '---\n'
	for item in items:
		s += item
	s += footer
	return s


def getSubList(reddit):
	bottiquette = reddit.subreddit('Bottiquette').wiki['robots_txt_json']
	bans = json.loads(bottiquette.content_md)

	with open(robots_path, 'w') as robots_w:
		json.dump(bans, robots_w)


def buildSubList(reddit):
	if time.time() - os.stat(robots_path)[stat.ST_MTIME] > DAY_IN_SECONDS:
		logging.info('refreshing robots.txt')
		getSubList(reddit)

	with open(robots_path) as robots_r:
		bans = json.load(robots_r)

	sub_list = 'all'
	for ban in bans["disallowed"] + bans["permission"] + bans["posts-only"]:
		sub_list += '-{}'.format(ban)

	return sub_list
	

def run_bot(reddit):
	logging.info("Getting comments...")

	sub_list = buildSubList(reddit)
	subs = reddit.subreddit(sub_list)
	for comment in subs.comments(limit = 1000):
		match = re.findall("!(?i)youtube\s+.*", comment.body)
		if match:
			logging.info("Found invocation in comment id: " + comment.id)
			inv = match[0]
			channel_name = inv.partition(' ')[-1]

			comment_file_r = open(commented_path, 'r')
			commented = True

			if comment.id not in comment_file_r.read().splitlines():
				logging.info('new invocation; running...\n')
				
				try:
					title, data = getYoutubeData(channel_name)
				except Exception as err:
					logging.exception('{}: {}'.format(type(err), err))
					commented = False
				else:
					data = map(prettifyItem, parseData(data))
					reply = buildComment(title, data)
					logging.info(reply)

					try:
						comment.reply(reply)
					except praw.exceptions.APIException as err:
						logging.exception('{}: {}'.format(type(err), err))
						if err.error_type == 'RATELIMIT':
							commented = False
					except Exception as err:
						logging.exception('{}: {}'.format(type(err), err))
						
			else:
				logging.info('already replied')
				commented = False

			comment_file_r.close()

			commented = False
			if commented:
				comment_file_w = open(commented_path, 'a+')
				comment_file_w.write(comment.id + '\n')
				comment_file_w.close()

			time.sleep(10)

	logging.info('waiting 60s...')
	time.sleep(60)


def main():
	logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
		format="%(asctime)-15s %(levelname)-8s %(message)s")
	reddit = authenticate()
	buildSubList(reddit)
	while True:
		run_bot(reddit)

if __name__ == '__main__':
	main()
