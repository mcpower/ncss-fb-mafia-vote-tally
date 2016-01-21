#!/usr/bin/env python
from __future__ import print_function
import requests
import re
import json
import os.path
import time
from jinja2 import Environment, FileSystemLoader

get_path = lambda x: os.path.join(os.path.dirname(__file__), x)
conf = open(get_path("config.txt")).readlines()
access_token, post_id, group_id, cutoff = [line.strip() for line in conf[:4]]
if len(conf) > 4:
	double_user = conf[4].strip()
else:
	double_user = None
player_file = [line.strip() for line in open(get_path("players.txt")).readlines()]
if player_file[0] == "WHITELIST":
	is_whitelist = True
	players = {player for player in player_file[1:] if not player.startswith("#")}
elif player_file[0] == "BLACKLIST":
	is_whitelist = False
	players = {player for player in player_file[1:] if not player.startswith("#")}
else:
	is_whitelist = False
	whitelist = set()

COMMENTS_TEMPLATE = "https://graph.facebook.com/v2.5/{group_id}_{post_id}/comments?fields=from,message,message_tags,created_time&limit=300&access_token={access_token}"
MEMBERS_TEMPLATE = "https://graph.facebook.com/v2.2/{group_id}/members?fields=id,name,picture{{url}}&limit=200&access_token={access_token}"
comments_url = COMMENTS_TEMPLATE.format(post_id=post_id, access_token=access_token, group_id=group_id)
members_url = MEMBERS_TEMPLATE.format(group_id=group_id, access_token=access_token)

vote_re = re.compile(r"\b(?P<is_unvote>UN)?VOTE( |[:;] |[:;])", re.I)
users = {}

class User:
	def __init__(self, fbid, name, picture=None):
		self.fbid = fbid # str
		self.name = name # str
		self.picture = picture
		self.voted_user = None # User

	def vote(self, voted):
		out = None
		if self.voted_user is not None:
			#print("WARNING:", self.name, "overwrote previous vote of", self.voted_user.name, "with", voted.name)
			out = self.voted_user
		self.voted_user = voted
		return out

	def unvote(self, voted):
		if self.voted_user == voted:
			self.voted_user = None
			return True
		else:
			return False

	def __str__(self):
		return self.name

	def __repr__(self):
		return "User('{}')".format(self.name)

def get_user(fbid, name=None):
	if fbid not in users:
		users[fbid] = User(fbid, name)
	return users[fbid]

members_request = requests.get(members_url)
json_members = members_request.json()["data"]
users = {json_member["id"]: User(json_member["id"], json_member["name"], json_member["picture"]["data"]["url"]) for json_member in json_members}

comments_request = requests.get(comments_url)
json_comments = comments_request.json()["data"]

users_values = users.values()
check_players = set(players) # a copy
for user in users_values:
	if user.name in check_players:
		check_players.remove(user.name)
for unfound_player in check_players:
	print("UNFOUND PLAYER:", unfound_player)

comments = []
# yes, I know classes are overkill for this, but dicts aren't that great for objects
class Comment:
	def __init__(self, fbid, message, user, time, message_tags=None, index=0):
		self.fbid = fbid
		self.message = message
		self.user = user
		self.time = time
		self.message_tags = message_tags
		self.index = index
		self.vote_details = []

	def get_fb_url(self):
		return "https://www.facebook.com/groups/{group_id}/permalink/{post_id}/?comment_id={fbid}&offset={offset}&total_comments={total_comments}".format(
			group_id=group_id, post_id=post_id, fbid=self.fbid, offset=((len(json_comments) - self.index - 1)/50*50), total_comments=len(json_comments))

	@classmethod
	def from_json(cls, data, index=0):
		return cls(
			data["id"],
			data["message"],
			get_user(data["from"]["id"], data["from"]["name"]),
			data["created_time"],
			data.get("message_tags", []),
			index
		)

overtime = time.strftime("%Y-%m-%dT%H:%M:%S+0000",time.gmtime()) >= cutoff
for i, json_comment in enumerate(json_comments):
	vote_finds = list(vote_re.finditer(json_comment["message"]))
	if not vote_finds:
		continue
	if not is_whitelist and json_comment["from"]["name"] in players:
		continue
	if is_whitelist and json_comment["from"]["name"] not in players:
		continue
	comment = Comment.from_json(json_comment, i)
	if comment.time >= cutoff:
		break

	tags = {tag["offset"]: get_user(tag["id"], tag["name"]) for tag in comment.message_tags}

	for vote in vote_finds:
		end = vote.end()
		if end in tags:
			voted = tags[end]
		else:
			possible_voted = [user for user in users_values if comment.message.lower().startswith(user.name.lower(), end)]
			if len(possible_voted) == 0:
				# print("Didn't find any users.")
				continue
			elif len(possible_voted) > 1:
				# print("Found more than one possible user:", ", ".join(str(user) for user in possible_voted))
				continue
			voted = possible_voted[0]
		if (is_whitelist and voted.name not in players) or (not is_whitelist and voted.name in players):
			print(comment.user, "tried to vote for ignored user", voted)
			print("Message:")
			print(comment.message)
			print()
			comment.vote_details.append(("ignored", (voted,)))
			continue
		if vote.group("is_unvote"):
			r = comment.user.unvote(voted)
			if r:
				# print(comment.user, "unvoted for", voted)
				comment.vote_details.append(("unvote", (voted,)))
			else:
				print("UNSUCCESSFUL UNVOTE:", comment.user, "whoopsied", voted, "(they voted for", comment.user.voted_user, "before)")
				print("Message:")
				print(comment.message)
				print()
				comment.vote_details.append(("no unvote", (voted, comment.user.voted_user))) # didn't unvote, previous
		else:
			r = comment.user.vote(voted)
			if r is not None:
				comment.vote_details.append(("overvote", (voted, r))) # voted, previous
			else:
				comment.vote_details.append(("vote", (voted,)))
	
	if comment.vote_details:
		comments.append(comment)

env = Environment(loader=FileSystemLoader(get_path("templates")), trim_blocks=True, lstrip_blocks=True)
filtered_users = [user for user in users_values if user.voted_user]
tally = {} # User: [User]
for user in filtered_users:
	if user.voted_user not in tally:
		tally[user.voted_user] = []
	tally[user.voted_user].append(user)
	if user.name == double_user:
		tally[user.voted_user].append(user)
no_voters = [user for user in users_values if user.voted_user is None and ((is_whitelist and user.name in players) or (not is_whitelist and user.name not in players))]
sorted_tally = sorted(tally.items(), key=lambda x: len(x[1]), reverse=True)
open(get_path("output/index.html"), "w").write(env.get_template("index.html").render(comments=comments, users=list(users_values), tally=sorted_tally, no_voters=no_voters, overtime=overtime))
