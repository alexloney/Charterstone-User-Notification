#!python3

import subprocess
import re
import json
import requests
import random
import urllib.parse
import Constants
import datetime
from threading import Thread
import time
import pyautogui

last_update = datetime.datetime.now()
charterstone = None

def check_update_delay():
    global last_update
    while True:
        minutes_diff = (datetime.datetime.now() - last_update).total_seconds() / 60.0
        if minutes_diff > 30:
            trigger_ifttt_alert('Alert: It has been more than 30 minutes since we\'ve seen an update, please check connectivity. {}')
            last_update = datetime.datetime.now()
        time.sleep(60)

def get_current_user(packet, game_id):

    # print('Getting current user')

    # Assemble the hex dump inot a hex string
    data = ''
    num = 0
    for row in packet:
        # Skipping first 5 rows since they could randomly contain "{" causing
        # the regex to fail
        num += 1
        if num < 5:
            continue
        match = re.match(r'.*([a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4} [a-f0-9]{4}).*', str(row))
        if match:
            data += match.group(1)
    data = data.replace(' ', '')

    # print('')

    # Convert the hex string into parsable data and search for a JSON string
    match = re.match(r'^[^\{]+(\{.*\})[^\}]+$', str(bytearray.fromhex(data)))
    if match:
        data = match.group(1).replace('\\\'', '\'')
        try:
            # print(data)
            # print('')
            data = json.loads(data)
            #print(data)
            #print('')
            #print('='*80)
        except json.JSONDecodeError:
            return
    else:
        return

    # We only care about our The Eventual Village game
    if not game_id in data:
        return

    current_user = data[game_id]['ha']['tn0']
    return current_user

def trigger_ifttt_alert(msg):
    ifttt_url = 'https://maker.ifttt.com/trigger/' + Constants.ALERT_APPLET + '/with/key/' + Constants.API_KEY
    payload = '?value1='

    msg = msg.format(Constants.ALERT_USER)

    payload += urllib.parse.quote(msg)
    requests.post(ifttt_url + payload)

    restart_charterstone()

def trigger_ifttt(user, game):
    ifttt_url = 'https://maker.ifttt.com/trigger/' + game['APPLET'] + '/with/key/' + Constants.API_KEY
    payload = '?value1='

    with open('msg.txt') as f:
        msg = random.choice(f.read().splitlines())
    
    if user in game['USERS']:
        try:
            msg = msg.format(game['USERS'][user])
        except IndexError:
            print('Index Error, user: ' + user)
            return
    else:
        print('Unable to locate user: ' + user + ' in game: ' + game['MAGIC'])
        return
    
    payload += urllib.parse.quote(msg)
    requests.post(ifttt_url + payload)

def restart_charterstone():
    global charterstone
    if charterstone is not None:
        charterstone.kill()
    
    charterstone = subprocess.Popen(('/home/lex/.steam/debian-installation/steamapps/common/Charterstone Digital Edition/Linux/Charterstone.x86_64'), stdout=subprocess.PIPE)
    print('Charterstone started, waiting 10 seconds...')
    time.sleep(10)

    print('Clicking on window titlebar')
    pyautogui.moveTo(444, 138)
    print(pyautogui.position())
    pyautogui.leftClick()
    time.sleep(3)

    print('Opening Online Games')
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(3)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')

    # print('clicking on saved games')
    # pyautogui.moveTo(902, 264)
    # print(pyautogui.position())
    # pyautogui.leftClick()

    print('Charterstone should be running now')


t = Thread(target=check_update_delay)
t.start()

p = subprocess.Popen(('sudo', 'tcpdump', 'udp', 'port', '5055', '-X'), stdout=subprocess.PIPE)
# charterstone = subprocess.call(['/home/lex/.steam/debian-installation/steamapps/common/Charterstone Digital Edition/Linux/Charterstone.x86_64'])
restart_charterstone()

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
                    last_update = datetime.datetime.now()

                    if len(last_user[game['MAGIC']]) == 0:
                        last_user[game['MAGIC']] = current_user[game['MAGIC']]
                        print(game['MAGIC'] + ': ' + last_user[game['MAGIC']])
                        # trigger_ifttt(current_user[game['MAGIC']], game)
                    elif last_user[game['MAGIC']] != current_user[game['MAGIC']]:
                        last_user[game['MAGIC']] = current_user[game['MAGIC']]
                        print('Update: ' + game['MAGIC'] + ': ' + last_user[game['MAGIC']])
                        trigger_ifttt(current_user[game['MAGIC']], game)

        packet = []
    else:
        packet.append(row.strip())
