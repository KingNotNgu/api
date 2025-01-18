from flask import Flask, jsonify, request, render_template_string
import time
import requests
import base64
import string
import secrets
import sqlite3
from markupsafe import escape

app = Flask(__name__)

def generate_random_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

random = generate_random_key()

def generate_api_key(ip):
    timestamp = str(int(time.time()))
    unique_string = ip + ':' + timestamp + random
    api_key = base64.b64encode(unique_string.encode()).decode()
    return api_key
def save_api_key(ip, api_key):
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    existing_key = cursor.fetchone()
    while existing_key:
        new_api_key = generate_api_key(ip)
        cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (new_api_key,))
        existing_key = cursor.fetchone()
        api_key = new_api_key
    timestamp = int(time.time())
    cursor.execute('''
    INSERT INTO api_keys (ip, api_key, timestamp)
    VALUES (?, ?, ?)
    ''', (ip, api_key, timestamp))
    conn.commit()
    conn.close()
def init_db():
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        api_key TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    ''')
    conn.commit()
    conn.close()
init_db()
@app.route('/generate_api_key', methods=['GET'])
def generate_api_key_endpoint():
    try:
        url = 'https://api.ipify.org'
        req = requests.get(url, timeout=3)
        if req.status_code != 200:
            return jsonify({'error': 'Cek'}), 500
        ip = req.text.strip()
        if not ip:
            return jsonify({'error': 'Cekx x2'}), 500
        api_key = generate_api_key(ip)
        save_api_key(ip, api_key)
        
        url1 = f'https://kingnotngu.github.io/kingweb/?key={api_key}'
        linkchinh = requests.get(f"https://yeumoney.com/QL_api.php?token=a6f62ee08685c27576f15c65504d4126c12d384f7ecd8fc69f49aea44fdbd6a6&format=json&url={url1}", timeout=3)
        link = linkchinh.json()
        ug = link.get("shortenedUrl")
        ug = escape(ug)
        return render_template_string(
            f"""
        <script>
            window.onload = function() {{
                var url = "{ug}";
                window.location.replace(url);  // Chuyển hướng trực tiếp trong tab hiện tại
            }};
        </script>
            """
        )
    except requests.RequestException as e:
        return jsonify({'error': 'Request to ipify failed', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/check_api_key', methods=['POST'])
def check_api_key():
    data = request.get_json()
    api_key = data.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    key = cursor.fetchone()
    if key:
        cursor.execute('DELETE FROM api_keys WHERE api_key = ?', (api_key,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'true','message': 'API key found and deleted successfully','ip': key[1],'timestamp': key[3]})#'deleted_api_key': api_key,
    else:
        conn.close()
        return jsonify({'status': 'false','error': 'API key not found'}), 404

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=8000)
