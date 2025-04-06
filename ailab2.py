from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import requests
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

API_TOKEN = "ud4r0trddsuk27u356v4489mfj"
PROJECT_ID = "67403"
MODEL_NAME = "object-detection-model-1"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def make_prediction(image_path):
    url = f"https://platform.sentisight.ai/api/predict/{PROJECT_ID}/{MODEL_NAME}/"
    headers = {
        "X-Auth-token": API_TOKEN,
        "Content-Type": "application/octet-stream"
    }
    with open(image_path, 'rb') as img_file:
        response = requests.post(url, headers=headers, data=img_file)
    print("API Response Status Code:", response.status_code)
    print("API Response Text:", response.text)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def draw_annotations(image_path, predictions):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for pred in predictions:
        label = pred['label']
        score = pred['score']
        x0, y0, x1, y1 = pred['x0'], pred['y0'], pred['x1'], pred['y1']
        draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
        draw.text((x0, y0 - 10), f"{label} ({score:.2f})", fill="red")
    return image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        predictions = make_prediction(file_path)
        if predictions:
            annotated_image = draw_annotations(file_path, predictions)
            img_io = io.BytesIO()
            annotated_image.save(img_io, 'JPEG')
            img_io.seek(0)
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        else:
            return "Error making prediction", 500
    return "File not allowed", 400

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
