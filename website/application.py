import sys
import traceback
import time
import boto3
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

application = Flask(__name__)

REGION = 'us-west-2'

s3 = boto3.resource('s3')
S3_BUCKET_NAME = 'turbo-carnival'

sns = boto3.client('sns', region_name=REGION)
SNS_ARN = 'arn:aws:sns:us-west-2:767736770298:turbo-carnival-process-replay'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('turbo-carnival')
player_table = dynamodb.Table('turbo-carnival-players')
    
# 2 megs max upload
application.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@application.route("/")
def index():
    try:
        replays = table.scan(Limit=10)['Items']
    except:
        replays = []
        traceback.print_exc(file=sys.stderr)
    return render_template("index.html", replays=replays)

@application.route("/player_replays/<playerid>")
def player_replays(playerid):
    key = boto3.dynamodb.conditions.Key('online_id').eq(int(playerid))
    try:
        replays = player_table.query(KeyConditionExpression=key)['Items']
    except:
        replays = []
        traceback.print_exc(file=sys.stderr)
    return render_template("player_replays.html", online_id=playerid, replays=replays)

@application.route("/find_player_by_handle/<handle>")
def player_handle_lookup(handle):
    key = boto3.dynamodb.conditions.Key('name').eq(handle)
    try:
        player_replays = player_table.query(IndexName='name-index', KeyConditionExpression=key)['Items']
    except:
        player_replays = []
        traceback.print_exc(file=sys.stderr)
    return render_template("find_player.html", handle=handle, player_replays=player_replays)

def allowed_file(filename):
    return filename.endswith(".replay")

@application.route("/upload", methods=['GET', 'POST'])
def upload_file():
    print request.method
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template("upload.html", error="No file found")
        file = request.files['file']
        print file.filename
        if file.filename == '':
            return render_template("upload.html", error="No file selected")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                replay_filename = "replays/" + filename
                s3.Bucket(S3_BUCKET_NAME).put_object(Key=replay_filename, Body=file)
            except:
                traceback.print_exc(file=sys.stderr)
                return render_template("upload.html", error="Upload failed. Try again later.")
            if request.args.get('bulk'):
                sendReplaySNS(filename.replace(".replay",""))
                return "Success"
            return redirect(url_for('view_replay', insecure_filename=filename.replace(".replay", "")))
        else:
            return render_template("upload.html", error="bad file type")
    if request.method == 'GET':
        return render_template("upload.html")

def sendReplaySNS(replay):
    # Trigger replay to be processed
    print("Trigger replay processing " + replay)
    try:
        print(sns.publish(TopicArn=SNS_ARN, Subject='replay', Message=replay))
    except:
        traceback.print_exc(file=sys.stderr)
    
@application.route("/view_replay/<insecure_filename>")
def view_replay(insecure_filename):
    filename = secure_filename(insecure_filename)
    obj = s3.Object(S3_BUCKET_NAME, "replay_csvs/" + filename + ".replay.csv")
    # Wait 2 minutes max
    for i in range(0,6):
        try:
            obj.load()
            return render_template("visualize.html", filename=filename)
        except:
            traceback.print_exc(file=sys.stderr)
        if i==0:
            sendReplaySNS(filename)
        time.sleep(20)
    return "Error replay did not process, please upload again"

@application.route("/get_replay_data/<insecure_filename>")
def get_replay_data(insecure_filename):
    filename = secure_filename(insecure_filename)
    csv_filename = "replay_csvs/" + filename + ".replay.csv"
    obj = s3.Object(S3_BUCKET_NAME, csv_filename)
    try:
        obj_dict = obj.get()
        text = obj_dict['Body'].read()
    except:
        traceback.print_exc(file=sys.stderr)
        text = ""
    return text

if __name__ == "__main__":
    application.run('0.0.0.0')
