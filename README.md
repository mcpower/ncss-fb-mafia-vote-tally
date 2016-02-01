# NCSS FB Mafia Vote Tally
Tallies the NCSS Mafia Facebook page votes.

Warning: extremely hacky and bad code.

# Prerequisites
You need a few things:
* Python 3
* Requests
* Jinja2

`pip` is your friend when installing the latter two.

You need to create these files:
* `config.txt`
* `players.txt`
* `voteweights.txt`

In `config.txt`:

```
access_token (FB access token)
post_id (id of tracked post)
group_id (id of group)
cutoff (the voting cutoff, like 2015-01-23T13:00:00+0000)
```

In `players.txt`, a list of full names in players.txt to blacklist/whitelist (separated by new lines). Start the file with either "BLACKLIST" or "WHITELIST".:

```
WHITELIST
Mark Zuckerberg
John Smith
```

In `voteweights.txt`, custom vote weights for each person (can be empty):

```
Mark Zuckerberg|3
```
