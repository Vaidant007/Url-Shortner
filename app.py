import hashlib
import qrcode
from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import requests

app = Flask(__name__)

# In-memory hashmap for URL storage
url_map = {}

# Folder for saving QR codes
QR_FOLDER = os.path.join('static', 'qr_codes')
os.makedirs(QR_FOLDER, exist_ok=True)

# Function to fetch ngrok public URL dynamically
def get_ngrok_url():
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        response.raise_for_status()  # Raise exception if status is not 200
        tunnels = response.json().get('tunnels', [])
        for tunnel in tunnels:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
        print("No HTTPS tunnel found.")
    except Exception as e:
        print(f"Failed to fetch ngrok URL: {e}")
    return "http://127.0.0.1:5000"  # Fallback to localhost if ngrok fails


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

    # Fetch ngrok public URL dynamically for each request
    base_url = get_ngrok_url()
    short_url = f"{base_url}/{short_hash}"

    # Generate QR Code
    qr = qrcode.make(short_url)
    qr_path = os.path.join(QR_FOLDER, f"{short_hash}.png")
    qr.save(qr_path)

    return jsonify({
        "short_url": short_url,
        "qr_code_url": url_for('static', filename=f'qr_codes/{short_hash}.png')
    })


@app.route('/<short_hash>')
def redirect_url(short_hash):
    original_url = url_map.get(short_hash)
    if original_url:
        return redirect(original_url)
    return "URL not found", 404


if __name__ == '__main__':
    app.run(debug=True)
