# NCSS FB Mafia Vote Tally
Tallies the NCSS Mafia Facebook page votes.

Warning: extremely hacky and bad code.

# Prerequisites
You need a few things:
* Python 2
* Requests
* Jinja2

`pip` is your friend when installing the latter two.

Put this in config.txt:

```
access_token (FB access token)
post_id (id of tracked post)
group_id (id of group)
cutoff (the voting cutoff, like 2015-01-23T13:00:00+0000)
```

and put a list of full names in players.txt to blacklist/whitelist. (separated by new lines). Make sure you start the file with either "BLACKLIST" or "WHITELIST" For example:

```
BLACKLIST
Mark Zuckerberg
```