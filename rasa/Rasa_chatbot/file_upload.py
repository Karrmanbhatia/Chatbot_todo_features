# file_upload.py - Optional standalone file upload server

from flask import Flask, request, jsonify
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set up a temporary directory to store uploaded files
UPLOAD_FOLDER = tempfile.mkdtemp()
print(f"Files will be uploaded to: {UPLOAD_FOLDER}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload_test_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        # Generate a unique filename
        filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "file_path": file_path
        })
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Enable CORS for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

if __name__ == '__main__':
    print("Starting file upload server...")
    print("Endpoint: http://localhost:5005/upload_test_file")
    app.run(debug=True, port=5005)