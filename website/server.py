import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
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
            return redirect(url_for('view_replay', filename=filename))
        else:
            return render_template("upload.html", error="bad file type")
    if request.method == 'GET':
        return render_template("upload.html")
    
@app.route("/view_replay/<filename>")
def view_replay(filename):
    return render_template("visualize.html", filename)

if __name__ == "__main__":
    app.run()

    
