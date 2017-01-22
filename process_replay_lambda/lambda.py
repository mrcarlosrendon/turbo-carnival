import os
import sys
import subprocess
import traceback
from shutil import copyfile

import boto3

s3 = boto3.resource('s3')
S3_BUCKET_NAME = 'turbo-carnival'

def lambda_handler(event, context):
    records = event['Records']
    for record in records:
        replay_key = record['Sns']['Message']
        print("Processed: " + process(replay_key))
    return "Done"

def process(replay_key):
    csv_filename = "replay_csvs/" + replay_key + ".replay.csv"
    print("Checking if already procssed " + csv_filename)
    obj = s3.Object(S3_BUCKET_NAME, csv_filename)
    try:
        obj.load()
    except:
        print("Replay not yet processed")
        pass

    try:
        replay_filename = "replays/" + replay_key + ".replay"
        tmp_filename = "/tmp/" + replay_key
        replay_obj = s3.Object(S3_BUCKET_NAME, replay_filename).download_file(tmp_filename)
    except:
        traceback.print_exc(file=sys.stderr)
        return "could not get replay from s3"
    
    tmp_replay_file = open("/tmp/" + replay_key, 'r')

    copyfile('/var/task/octane', '/tmp/octane')
    os.chmod('/tmp/octane', 0555)
    p1 = subprocess.Popen(['/tmp/octane'], stdin=tmp_replay_file, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['python', 'rocket_league_replay_decode.py'],  
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p1.wait()
    output = p2.communicate()[0]
    tmp_replay_file.close()
    os.remove(tmp_filename)
    if not p1.returncode == 0 or not p2.returncode == 0: 
        return "pipeline fail " + str(p1.returncode) + " " + str(p2.returncode)

    try:
        s3.Bucket(S3_BUCKET_NAME).put_object(Key=csv_filename, Body=output)
    except:
        traceback.print_exc(file=sys.stderr)
        return "s3 upload failed"
    return csv_filename
