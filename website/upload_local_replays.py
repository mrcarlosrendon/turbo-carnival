""" Pull replay from rocketleaguereplays and post turbo-carnival """
import StringIO
import os
import sys
import traceback
import requests
import boto3

# To setup your keys
# aws configure
DYNAMO = boto3.resource("dynamodb")
TABLE = DYNAMO.Table('turbo-carnival')

REPLAY_DIR = "C:\Users\Carlos\Documents\My Games\Rocket League\TAGame\Demos"

def getReplay(replay_dir, replay_filename):
    """ Grabs an individual replay and posts to turbo-carnival"""
    files = {'file': open(replay_dir + "\\" + replay_filename, 'rb')}
    post = requests.post("http://rocketleague.carlosrendon.me/upload?bulk=true", files=files)
    if str(post.status_code) != '200':
        print("upload failed: " + str(post.status_code))

def getAllReplays(replay_dir):
    """ Get's all of the replays """
    for replay_file in os.listdir(replay_dir):
        print(replay_file)
        replay = replay_file.replace(".replay","")
        try:
            ret = TABLE.get_item(Key={"replay_key": replay})
        except:
            traceback.print_exc(file=sys.stderr)
            exit(1)
        if not ret.has_key('Item'):
           print("Grabbing " + replay)
           getReplay(replay_dir, replay_file)
        else:
            print("Skipping " + replay)

getAllReplays(REPLAY_DIR)
