import sys
import time
import traceback
import boto3

REGION = 'us-west-2'

s3 = boto3.client('s3')
S3_BUCKET_NAME = 'turbo-carnival'

sns = boto3.client('sns', region_name=REGION)
SNS_ARN = 'arn:aws:sns:us-west-2:767736770298:turbo-carnival-process-replay'

def getListOfReplays(nextToken=None):
    replays = []
    resp = None
    try:
        if nextToken:
            resp = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='replays', ContinuationToken=nextToken)
        else:
            resp = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='replays')
    except:
        traceback.print_exc(file=sys.stderr)
    
    if resp:
        for item in resp['Contents']:
            name = item['Key'].replace("replays/","").replace(".replay","")
            replays.append(name)
        truncated = resp['IsTruncated']
        if truncated:
            nextToken = resp['NextContinuationToken']
            print("Continuation: " + nextToken)
            more_replays = getListOfReplays(nextToken=nextToken)
            for replay in more_replays:
                replays.append(replay)
    return replays

def sendReplaySNS(replay):
    # Trigger replay to be processed
    print("Trigger replay processing " + replay)
    try:
        print(sns.publish(TopicArn=SNS_ARN, Subject='replay', Message=replay))
    except:
        traceback.print_exc(file=sys.stderr)

replays = getListOfReplays()

i = 0
for replay in replays:
    sendReplaySNS(replay)
    i = i+1
    # 60 writes per second with 1 dynamo write capacity unit
    # say 6 writes per replay and also to secondary index
    # 6 writes per second per replay
    # Wait 8 seconds per replay to leave a little buffer
    time.sleep(6)
