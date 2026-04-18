import os
import numpy as np
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D
import cv2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs('static/uploads/query', exist_ok=True)
os.makedirs('static/uploads/dataset', exist_ok=True)

# Load MobileNetV2 model for feature extraction
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
model = Model(inputs=base_model.input, outputs=GlobalAveragePooling2D()(base_model.output))

def extract_features(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    img_data = preprocess_input(img_data)
    return model.predict(img_data).flatten()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_img = request.files['query']
        dataset_imgs = request.files.getlist('dataset')

        query_path = os.path.join(app.config['UPLOAD_FOLDER'], 'query', secure_filename(query_img.filename))
        query_img.save(query_path)

        dataset_paths = []
        for img in dataset_imgs:
            path = os.path.join(app.config['UPLOAD_FOLDER'], 'dataset', secure_filename(img.filename))
            img.save(path)
            dataset_paths.append(path)

        query_features = extract_features(query_path)

        similarities = []
        for path in dataset_paths:
            features = extract_features(path)
            similarity = np.linalg.norm(query_features - features)
            similarities.append((path, similarity))

        # Sort by similarity (lower distance = more similar)
        similarities.sort(key=lambda x: x[1])
        top_5 = [os.path.basename(path) for path, _ in similarities[:5]]

        return render_template('index.html', query_image=os.path.basename(query_path), similar_images=top_5)

    return render_template('index.html', query_image=None)

if __name__ == '__main__':
    app.run(debug=True)