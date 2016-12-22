import os
import subprocess
import boto3
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

application = Flask(__name__)

s3 = boto3.resource('s3')
S3_BUCKET_NAME = 'turbo-carnival'

if os.name == 'nt':
    application.config['UPLOAD_FOLDER'] = 'C:/Users/Carlos/Documents/GitHub/turbo-carnival/website/uploads'    
else:
    application.config['UPLOAD_FOLDER'] = '/app/uploads'
    
# 2 megs max
application.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@application.route("/")
def index():
    return render_template("index.html")

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
                s3.Bucket(S3_BUCKET_NAME).put_object(Key="replays/" + filename, Body=file)
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
    in_filename = os.path.join(application.config['UPLOAD_FOLDER'], filename)
    json_filename = os.path.join(application.config['UPLOAD_FOLDER'], filename + ".json")
    csv_filename = os.path.join(application.config['UPLOAD_FOLDER'], filename + ".csv")

    filename = secure_filename(insecure_filename)
    obj = s3.Object(S3_BUCKET_NAME, filename + ".csv")
    try:
        obj.load()
        return render_template("visualize.html", filename=filename)
    except:
        print("it's cool")
        
    
    octane_in = open(in_filename, "r")
    octane_out = open(json_filename, "w")
    
    res = subprocess.call(['octane'], stdin=octane_in, stdout=octane_out)
    if res == 0:
        csv_in = open(json_filename, "r")
        csv_out = open(csv_filename, "w")
        res = subprocess.call(['python', '../rocket_league_replay_decode.py'], stdin=csv_in, stdout=csv_out)
        if res == 0:
            return render_template("visualize.html", filename=filename)
    return "error processing"

@application.route("/get_replay_data/<insecure_filename>")
def get_replay_data(insecure_filename):
    filename = secure_filename(insecure_filename)
    obj = s3.Object(S3_BUCKET_NAME, "replay_csvs" + filename + ".csv")
    text = ""
    try:
        obj_dict = obj.get()
        text = obj_dict['Body'].read()
    except:
        text = ""
    return text

if __name__ == "__main__":
    application.run('0.0.0.0')

    
