import asyncio
import logging
import time
from collections import defaultdict
import ipaddress
from flask import Flask, jsonify, request, render_template_string
import base64
import hmac
import hashlib
import string
import secrets
import sqlite3
import os

app = Flask(__name__)

HOST = '0.0.0.0'
PORT = 8000
RATE_LIMIT_REQUESTS = 10  
RATE_LIMIT_WINDOW = 1   
BANDWIDTH_LIMIT = 10 * 1024 * 1024 
WHITELIST = ['127.0.0.1', '192.168.1.0/24']
BLACKLIST = ['10.0.0.1', '172.16.0.0/16']
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
request_counts = defaultdict(lambda: {"count": 0, "last_reset": 0})
bandwidth_usage = defaultdict(float) 
blocked_ips = set()
WHITELIST = [ipaddress.ip_network(ip) for ip in WHITELIST]
BLACKLIST = [ipaddress.ip_network(ip) for ip in BLACKLIST]

def is_ip_allowed(ip):
    ip_obj = ipaddress.ip_address(ip)
    if any(ip_obj in network for network in BLACKLIST):
        return False
    if WHITELIST and not any(ip_obj in network for network in WHITELIST):
        return False
    return True

def check_rate_limit(ip):
    """Kiểm tra số request trong khoảng thời gian giới hạn."""
    now = time.time()
    if now - request_counts[ip]["last_reset"] > RATE_LIMIT_WINDOW:
        request_counts[ip] = {"count": 1, "last_reset": now}
        return True
    elif request_counts[ip]["count"] < RATE_LIMIT_REQUESTS:
        request_counts[ip]["count"] += 1
        return True
    else:
        return False

def check_bandwidth_limit(ip, data_size):
    """Cập nhật và kiểm tra băng thông IP."""
    bandwidth_usage[ip] += data_size
    if bandwidth_usage[ip] > BANDWIDTH_LIMIT:
        logger.warning(f"IP {ip} vượt quá giới hạn băng thông, chặn kết nối.")
        blocked_ips.add(ip)
        return True
    return False

def generate_random_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_api_key(ip, user_key):
    unique_string = f"{user_key}:{ip}"
    secret = os.urandom(10).hex()
    # api_key = base64.b64encode(unique_string.encode()).decode()
    api_key = hmac.new(secret.encode(), unique_string.encode(), hashlib.sha256).hexdigest()
    return api_key

def save_api_key(ip, user_key):
    api_key = generate_api_key(ip, user_key)
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    existing_key = cursor.fetchone()

    while existing_key:
        api_key = generate_api_key(ip, user_key)
        cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
        existing_key = cursor.fetchone()
    timestamp = int(time.time())
    cursor.execute('''
    INSERT INTO api_keys (ip, api_key, original_key, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (ip, api_key, user_key, timestamp))
    conn.commit()
    conn.close()
    return api_key
def reset_db():
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS api_keys')  # Xoá bảng cũ nếu tồn tại
    cursor.execute('''
    CREATE TABLE api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        api_key TEXT NOT NULL,
        original_key TEXT NOT NULL,  -- Cột mới đã thêm vào
        timestamp INTEGER NOT NULL
    )
    ''')
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
        original_key TEXT NOT NULL,  -- Đảm bảo rằng cột này tồn tại
        timestamp INTEGER NOT NULL
    )
    ''')
    conn.commit()
    conn.close()
# def init_db():
#     conn = sqlite3.connect('api_keys.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#     CREATE TABLE IF NOT EXISTS api_keys (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         ip TEXT NOT NULL,
#         api_key TEXT NOT NULL,
#         original_key TEXT NOT NULL,  -- Đảm bảo rằng cột này tồn tại
#         timestamp INTEGER NOT NULL
#     )
#     ''')
#     conn.commit()
#     conn.close()

init_db()
MAX_PAYLOAD_SIZE = 1024  # 1 KB
@app.before_request
def limit_payload_size():
    if request.content_length and request.content_length > MAX_PAYLOAD_SIZE:
        return jsonify({'error': 'ddos hmmm?'}), 413
@app.route('/generate_api_key', methods=['GET'])
def generate_api_key_endpoint():
    try:
        user_key = request.args.get('key')
        ip_param = request.remote_addr
        if not ip_param:
            return jsonify({'error': 'IP address not found'}), 500
        if not user_key:
            return jsonify({'error': 'User key is required'}), 400
        if ip_param in blocked_ips or not is_ip_allowed(ip_param):
            return jsonify({'error': 'Access denied'}), 403
        if not check_rate_limit(ip_param):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        api_key = save_api_key(ip_param, user_key)
        url_to_shorten = f'https://kingnotngu.github.io/kingweb/?key={api_key}'
        # html_content = f"""
        # <!DOCTYPE html>
        # <html>
        # <head>
        #     <title>Redirecting...</title>
        #     <meta http-equiv="refresh" content="0;url={url_to_shorten}" />
        # </head>
        # <body>
        #     <p>If you are not redirected automatically, click <a href="{url_to_shorten}">here</a>.</p>
        # </body>
        # </html>
        # """
        html_content = f"""
            <script>
                window.onload = function() {{
                    var url = "{url_to_shorten}";
                    window.location.replace(url);
                }};
            </script>
            """
        return html_content, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/generate_api_key2', methods=['GET'])
def generate_api_key_endpoint1():
    try:
        user_key = request.args.get('key')
        ip_param = request.remote_addr
        if not ip_param:
            return jsonify({'error': 'IP address not found'}), 500
        if not user_key:
            return jsonify({'error': 'User key is required'}), 400
        if ip_param in blocked_ips or not is_ip_allowed(ip_param):
            return jsonify({'error': 'Access denied'}), 403
        if not check_rate_limit(ip_param):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        api_key = save_api_key(ip_param, user_key)
        url_to_shorten = f'https://kingnotngu.github.io/kingweb/?key=?ug%20{api_key}'
        html_content = f"""
            <script>
                window.onload = function() {{
                    var url = "{url_to_shorten}";
                    window.location.replace(url);
                }};
            </script>
            """
        return html_content, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/check_api_key', methods=['POST'])
def check_api_key():
    data = request.get_json()
    api_key = data.get('key')  # Lấy API Key từ body của yêu cầu POST
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    existing_key = cursor.fetchone()
    conn.close()

    if existing_key:
        return jsonify({
            'valid': True, 
            'message': 'Key is valid',
            'ip': existing_key[1],  # Trả về IP của người dùng
            'key': existing_key[3]  # Trả về user_key (khóa gốc)
        }), 200
    else:
        return jsonify({'valid': False}), 404

@app.route('/delete_api_key', methods=['POST'])
def delete_api_key():
    data = request.get_json()
    api_key = data.get('key')
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    try:
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()

        # Tìm tất cả các API key có nội dung trùng khớp
        cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
        matching_keys = cursor.fetchall()

        if not matching_keys:
            conn.close()
            logger.warning(f"API key {api_key} không tồn tại.")
            return jsonify({'error': 'API key not found'}), 404

        # Xóa tất cả các API key trùng khớp
        cursor.execute('DELETE FROM api_keys WHERE api_key = ?', (api_key,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"{rows_deleted} API key(s) giống {api_key} đã bị xóa thành công.")
        return jsonify({'message': f'{rows_deleted} API key(s) deleted successfully'}), 200

    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
