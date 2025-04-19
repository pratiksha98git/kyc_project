from flask import Flask, request, jsonify,render_template
from app.database import get_db  
from bson.objectid import ObjectId
from PIL import Image
import pytesseract
import pymongo
import os

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 


db = get_db()
users = db['users']
kyc = db['kyc_data']

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

# Route to serve registration page
@app.route('/register-page')
def register_page():
    return render_template('register.html')

# Route to serve KYC upload page
@app.route('/upload-kyc-page')
def upload_kyc_page():
    return render_template('upload_kyc.html')

# Route to view all KYC records for a given username
@app.route('/kyc-records-page')
def kyc_records_page():
    return render_template('kyc_records.html')

# Route to view KYC details for a given doc_id
@app.route('/kyc-details-page')
def kyc_details_page():
    return render_template('kyc_details.html')



# Register API
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    if users.find_one({'username': data['username']}):
        return jsonify({'status': 'error', 'message': 'User already exists'})
    users.insert_one({
        'username': data['username'],
        'password': data['password'],   # Add this if password is in the form
        'dob': data['dob']
    })
    return jsonify({'status': 'success', 'message': 'User registered'})


# Login API
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user = users.find_one({'username': data['username'], 'password': data['password']})
    if user:
        return jsonify({'status': 'success', 'message': 'Login successful'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'})

# Upload PAN/Aadhaar and extract KYC data
@app.route('/upload-kyc', methods=['POST'])
def upload_kyc():
    username = request.form['username']
    file = request.files['kyc_doc']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Run OCR
    text = pytesseract.image_to_string(Image.open(filepath))

    # Basic parsing
    kyc_info = {
        'username': username,
        'image_filename': file.filename,
        'raw_text': text,
        'name': find_line_with(text, 'name'),
        'dob': find_line_with(text, 'dob'),
        'id_number': find_line_with(text, 'number'),
        'gender': find_line_with(text, 'gender'),
        'father_name': find_line_with(text, "father")
    }

    # Save to DB
    kyc.insert_one(kyc_info)
    return jsonify({'status': 'success', 'message': 'KYC uploaded'})

# Show all records for a user
@app.route('/kyc-records/<username>', methods=['GET'])
def kyc_records(username):
    records = list(kyc.find({'username': username}, {'_id': 0}))
    return jsonify({'status': 'success', 'records': records})

@app.route('/kyc-details/<doc_id>', methods=['GET'])
def kyc_details(doc_id):
    try:
        record = kyc.find_one({'_id': ObjectId(doc_id)}, {'_id': 0})
        if record:
            return jsonify({'status': 'success', 'record': record})
        return jsonify({'status': 'error', 'message': 'Record not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Invalid document ID'})

# Utility to match text lines
def find_line_with(text, keyword):
    for line in text.split('\n'):
        if keyword.lower() in line.lower():
            return line.strip()
    return 'Not Found'

if __name__ == '__main__':
    app.run(port=5007,debug=True)
