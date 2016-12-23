import os
import sys
import subprocess
import boto3
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

application = Flask(__name__)

s3 = boto3.resource('s3')
S3_BUCKET_NAME = 'turbo-carnival'
    
# 2 megs max upload
application.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@application.route("/")
def index():
    try:
        replays = s3.Bucket(S3_BUCKET_NAME).objects.filter(Prefix="replays", MaxKeys=10)
    except:
        replays = []
    replay_links = []
    for replay in replays:
        if replay.key.endswith(".replay"):
            after_path = replay.key.split("/")[1]
            replay_links.append(url_for('view_replay', insecure_filename=after_path))
    return render_template("index.html", recent_list=replay_links)

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
                return render_template("upload.html", error="Upload failed. Try again later.")
            return redirect(url_for('view_replay', insecure_filename=filename))
        else:
            return render_template("upload.html", error="bad file type")
    if request.method == 'GET':
        return render_template("upload.html")
    
@application.route("/view_replay/<insecure_filename>")
def view_replay(insecure_filename):
    filename = secure_filename(insecure_filename)
    obj = s3.Object(S3_BUCKET_NAME, filename + ".csv")
    try:
        obj.load()
        return render_template("visualize.html", filename=filename)
    except:
        pass

    try:
        replay_filename = "replays/" + filename
        tmp_filename = "/tmp/" + filename
        replay_obj = s3.Object(S3_BUCKET_NAME, replay_filename).download_file(tmp_filename)
    except:
        return "could not get replay from s3"
    
    tmp_replay_file = open("/tmp/" + filename, 'r')

    p1 = subprocess.Popen(['octane'], stdin=tmp_replay_file, stdout=subprocess.PIPE)
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
        csv_filename = "replay_csvs/" + filename + ".csv"
        s3.Bucket(S3_BUCKET_NAME).put_object(Key=csv_filename, Body=output)
    except:
        return "s3 upload failed"

    return render_template("visualize.html", filename=filename)

@application.route("/get_replay_data/<insecure_filename>")
def get_replay_data(insecure_filename):
    filename = secure_filename(insecure_filename)
    csv_filename = "replay_csvs/" + filename + ".csv"
    obj = s3.Object(S3_BUCKET_NAME, csv_filename)
    try:
        obj_dict = obj.get()
        text = obj_dict['Body'].read()
    except:
        text = ""
    return text

if __name__ == "__main__":
    application.run('0.0.0.0')

    
