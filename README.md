# Charterstone User Notification
This is a very simple project to implement a notification option that integrates with Discord Discord.
The reason for this is because the Charterstone program has very poor notification settings, sometimes
(many times) sending false alerts or not notifying at all.

This application takes advantage of the fact that Charterstone communicates with their backend systems
in an unencrypted way over UDP port 5055. While I do not understand the full structure of these packets,
I don't really need to. I've been able to locate that they contain a JSON encoded payload which contains
details about the games that you're actively watching, including the next player to move. This is done
by using the `tcpdump` program and just capturing the STDOUT from it in Python, then parsing that. It will
dump output as a hex dump of each packet sent/received. With that hex dump, I convert it into binary data
and look for the pattern `{...}`, then attempt to parse that as JSON.

So what this does is monitor that port on UDP protocol and parses out potential JSON payloads. From
there, it will then look for a game ID in the paload and if it's located, it will look up the next user
to move and fire off an IFTTT event that will forward a notification to Discord. Using IFTTT was much
simpler to do than writing my own Discord bot in addition to this, since I really just needed to send
a message to a chat when an event occurs.

In addition to sending a message, it uses the `Constants.py` script (not included in this repo for obvious
reasons) to look up the user and obtain the correct tag (in the form <@ID>) for the user. It then reads
the `msg.txt` file and picks a random line to use as the message, replacing `{}` with the tag. I split
the messages into their own file so that I may edit/add to them whenever without having to restart the
Python script.

In order to run the Python script, simply create a `Constants.py` that looks like the following:
```
GAME_MAGIX = '...'
APPLET_NAME = 'Get this from IFTTT WebApplet'
API_KEY = 'Get this from IFTTT, select Documentation to see it'
USERS = {
    'Name as seen in Charterstone': '<@Discord ID>',
    'Name as seen in Charterstone': '<@Discord ID>',
    'Name as seen in Charterstone': '<@Discord ID>',
    ...
}
```

Then execute the Python script with:
```
sudo python3 main.py
```

Finally, open Charterstone and log into the online section. Once logged in, leave Charterstone running,
it will automatically ping the server list and the Python script will monitor the traffic, sending
alerts as players change.

One last thing to point out, if you were able to reverse engineer the Charterstone data transfer
protocol, it would be possible to do all of this directly in Python instead of having to keep the
Charterstone program open. However, that is more work than I want to put into such a small project, so
I'm satisfied with the way this currently works. That said, if you DO decide to pursue that, so far
as I can tell, Charterstone is using [Photon](https://www.photonengine.com/) for the backend, so you
could likely look into the Photon documentation and determine exactly how it provides communications.
