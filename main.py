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
            # print(data)
        except json.JSONDecodeError:
            return
    else:
        return

    # We only care about our The Eventual Village game
    if not game_id in data:
        return

    current_user = data[game_id]['ha']['tn0']
    return current_user

def trigger_ifttt(user, game):
    ifttt_url = 'https://maker.ifttt.com/trigger/' + game['APPLET'] + '/with/key/' + Constants.API_KEY
    payload = '?value1='

    with open('msg.txt') as f:
        msg = random.choice(f.read().splitlines())
    
    if user in game['USERS']:
        msg = msg.format(game['USERS'][user])
    else:
        print('Unable to locate user: ' + user + ' in game: ' + game['MAGIC'])
        return
    
    payload += urllib.parse.quote(msg)
    requests.post(ifttt_url + payload)

p = subprocess.Popen(('tcpdump', 'udp', 'port', '5055', '-X'), stdout=subprocess.PIPE)

last_user = {}
current_user = {}
for game in Constants.GAMES:
    last_user[game['MAGIC']] = ''
    current_user[game['MAGIC']] = ''

packet = []
for row in iter(p.stdout.readline, b''):
    if b': UDP, length ' in row:
        if len(packet) > 0:
            for game in Constants.GAMES:
                current_user[game['MAGIC']] = get_current_user(packet, game['MAGIC'])

                if current_user[game['MAGIC']] is not None:
                    if len(last_user[game['MAGIC']]) == 0:
                        last_user[game['MAGIC']] = current_user[game['MAGIC']]
                        print(game['MAGIC'] + ': ' + last_user[game['MAGIC']])
                        continue
                    elif last_user[game['MAGIC']] != current_user[game['MAGIC']]:
                        last_user[game['MAGIC']] = current_user[game['MAGIC']]
                        print('Update: ' + game['MAGIC'] + ': ' + last_user[game['MAGIC']])
                        trigger_ifttt(current_user[game['MAGIC']], game)

        packet = []
    else:
        packet.append(row.strip())
