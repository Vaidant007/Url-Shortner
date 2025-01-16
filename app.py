import hashlib
import qrcode
from flask import Flask, request, jsonify, render_template, redirect, url_for
import os

app = Flask(__name__)

# In-memory hashmap for URL storage
url_map = {}

# Folder for saving QR codes
QR_FOLDER = os.path.join('static', 'qr_codes')
os.makedirs(QR_FOLDER, exist_ok=True)

# Get Base URL (Use Render's Environment Variable)
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://127.0.0.1:5000")  # Fallback to localhost

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.json.get('url')
    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    # Generate a unique hash for the URL
    short_hash = hashlib.md5(original_url.encode()).hexdigest()[:6]
    url_map[short_hash] = original_url

    # Use Render URL instead of Ngrok
    short_url = f"{BASE_URL}/{short_hash}"

    # Generate QR Code
    qr = qrcode.make(short_url)
    qr_path = os.path.join(QR_FOLDER, f"{short_hash}.png")
    qr.save(qr_path)

    return jsonify({
        "short_url": short_url,
        "qr_code_url": url_for('static', filename=f'qr_codes/{short_hash}.png', _external=True)
    })

@app.route('/<short_hash>')
def redirect_url(short_hash):
    original_url = url_map.get(short_hash)
    if original_url:
        return redirect(original_url)
    return "URL not found", 404

if __name__ == '__main__':
    app.run(debug=True)
