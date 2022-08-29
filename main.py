#!python3

import subprocess
import re
import json
import requests
import random
import urllib.parse
import Constants

def get_current_user(packet, game_id):

    # Assemble the hex dump inot a hex string
    data = ''
    for row in packet:
        match = re.match(r'.*([a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4}).*', str(row))
        if match:
            data += match.group(1)
    data = data.replace(' ', '')

    # Convert the hex string into parsable data and search for a JSON string
    match = re.match(r'^[^\{]+(\{.*\})[^\}]+$', str(bytearray.fromhex(data)))
    if match:
        data = match.group(1).replace('\\\'', '\'')
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return
    else:
        return

    # We only care about our The Eventual Village game
    if not game_id in data:
        return

    current_user = data[game_id]['ha']['tn0']
    return current_user

def trigger_ifff(user):
    ifttt_url = 'https://maker.ifttt.com/trigger/' + Constants.APPLET_NAME + '/with/key/' + Constants.API_KEY
    payload = '?value1='

    with open('msg.txt') as f:
        messages = f.read().splitlines()

    msg = random.choice(messages)

    if user in Constants.USERS:
        msg = msg.format(Constants.USERS[user])
    else:
        print('Unable to locate user: ' + user)
        return

    payload += urllib.parse.quote(msg)
    requests.post(ifttt_url + payload)


p = subprocess.Popen(('tcpdump', 'udp', 'port', '5055', '-X'), stdout=subprocess.PIPE)

last_user = ''
packet = []
for row in iter(p.stdout.readline, b''):
    if b': UDP, length ' in row:
        if len(packet) > 0:
            current_user = get_current_user(packet, Constants.GAME_MAGIC)
            if current_user is not None:
                if len(last_user) == 0:
                    last_user = current_user
                    print('First: ' + last_user)
                    continue
                elif last_user != current_user:
                    last_user = current_user
                    print('Update: ' + last_user)
                    trigger_ifff(current_user)
        packet = []
    else:
        packet.append(row.strip())
