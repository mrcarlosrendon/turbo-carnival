import os
import subprocess
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

if os.name == 'nt':
    app.config['UPLOAD_FOLDER'] = 'C:/Users/Carlos/Documents/GitHub/turbo-carnival/website/uploads'    
else:
    app.config['UPLOAD_FOLDER'] = '/app/uploads'
    
# 2 megs max
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@app.route("/")
def index():
    return render_template("index.html")

def allowed_file(filename):
    return filename.endswith(".replay")

@app.route("/upload", methods=['GET', 'POST'])
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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('view_replay', insecure_filename=filename))
        else:
            return render_template("upload.html", error="bad file type")
    if request.method == 'GET':
        return render_template("upload.html")
    
@app.route("/view_replay/<insecure_filename>")
def view_replay(insecure_filename):
    filename = secure_filename(insecure_filename)
    in_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    json_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename + ".json")
    csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename + ".csv")

    if os.path.isfile(csv_filename):
        return render_template("visualize.html", filename=filename)
    
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

@app.route("/get_replay_data/<insecure_filename>")
def get_replay_data(insecure_filename):
    filename = secure_filename(insecure_filename)
    csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename + ".csv")
    csv = open(csv_filename, "r")
    text = csv.read()
    return text

if __name__ == "__main__":
    app.run('0.0.0.0')

    
