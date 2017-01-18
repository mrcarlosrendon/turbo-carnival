""" Pull replay from rocketleaguereplays and post turbo-carnival """
import StringIO
import time
import requests
import boto3

# To setup your keys
# aws configure --profile turbo-carnival
SESSION = boto3.Session(profile_name='turbo-carnival')
DYNAMO = SESSION.resource("dynamodb")
TABLE = DYNAMO.Table('turbo-carnival')

def getReplay(replay_hash):
    """ Grabs an individual replay and posts to turbo-carnival"""
    url = "https://media.rocketleaguereplays.com/uploads/replay_files/" + replay_hash + ".replay"
    req = requests.get(url)
    if str(req.status_code) == '200':
        str_file = StringIO.StringIO(req.content)
        files = {"file": (replay_hash + ".replay", str_file)}
        post = requests.post("http://rocketleague.carlosrendon.me/upload", files=files)
        if str(post.status_code) != '200':
            print("upload failed: " + str(post.status_code))
    else:
        print("download failed: " + str(req.status_code))

def listRLReplays(page):
    """ Grabs a list of replay hashs from the RL replays API."""
    if page == 1:
        req = requests.get("http://www.rocketleaguereplays.com/api/replays")
    else:
        req = requests.get("http://www.rocketleaguereplays.com/api/replays?page=" + str(page))
    if str(req.status_code) != '200':
        print("Error querying api: " + str(req.status_code))
        print(req.content)
        return []
    resp = req.json()

    ids = []
    for result in resp['results']:
        if result['replay_id']:
            ids.append(result['replay_id'])
    return ids

def getAllReplays():
    """ Get's all of the replays. Handle's API paging."""
    page = 1
    while True:
        replays = listRLReplays(page)
        for replay in replays:
            try:
                ret = TABLE.get_item(Key={"replay_key": replay})
            except:
                print("Exception")
                exit(1)
            if not ret.has_key('Item'):
                print("Grabbing " + replay)
                getReplay(replay)
                time.sleep(10)
            else:
                print("Skipping " + replay)
        page = page + 1

getAllReplays()
