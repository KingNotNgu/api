# from flask import Flask, jsonify, render_template_string, request
# import requests
# from markupsafe import escape
# import base64
# import string
# import secrets
# import time
# import sqlite3

# app = Flask(__name__)

# def generate_random_key(length=6):
#     characters = string.ascii_letters + string.digits
#     return ''.join(secrets.choice(characters) for _ in range(length))

# random = generate_random_key()

# def generate_api_key(ip, user_key):
#     unique_string = f"{user_key}:{ip}"
#     api_key = base64.b64encode(unique_string.encode()).decode()
#     return api_key
# def generate_api_keykid(ip):
#     timestamp = str(int(time.time()))
#     unique_string = ip + ':' + timestamp + random
#     api_key = base64.b64encode(unique_string.encode()).decode()
#     return api_key

# def save_api_key(ip, api_key):
#     conn = sqlite3.connect('api_keys.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
#     existing_key = cursor.fetchone()
#     while existing_key:
#         new_api_key = generate_api_key(ip)
#         cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (new_api_key,))
#         existing_key = cursor.fetchone()
#         api_key = new_api_key
#     timestamp = int(time.time())
#     cursor.execute('''
#     INSERT INTO api_keys (ip, api_key, timestamp)
#     VALUES (?, ?, ?)
#     ''', (ip, api_key, timestamp))
#     conn.commit()
#     conn.close()

# def init_db():
#     conn = sqlite3.connect('api_keys.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#     CREATE TABLE IF NOT EXISTS api_keys (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         ip TEXT NOT NULL,
#         api_key TEXT NOT NULL,
#         timestamp INTEGER NOT NULL
#     )
#     ''')
#     conn.commit()
#     conn.close()

# init_db()

# @app.route('/generate_api_key', methods=['GET'])
# def generate_api_key_endpoint():
#     try:
#         user_key = request.args.get('key')
#         ip_param = request.remote_addr
#         if not ip_param:
#             return jsonify({'error': 'Hello world'}), 500
#         if not user_key:
#             return jsonify({'error': '404'}), 400
#         api_key = generate_api_key(ip_param, user_key)
#         url_to_shorten = f'https://kingnotngu.github.io/kingweb/?key={api_key}'
#         url_to_shorten = escape(url_to_shorten)
#         return render_template_string(
#             f"""
#             <script>
#                 window.onload = function() {{
#                     var url = "{url_to_shorten}";
#                     window.location.replace(url);
#                 }};
#             </script>
#             """)
#     except requests.RequestException as e:
#         return jsonify({'error': 'Yêu cầu thất bại', 'details': 'Cek'}), 500
#     except Exception as e:
#         return jsonify({'error': 'Đã xảy ra lỗi không mong đợi', 'details': 'cekx2'}), 500

# @app.route('/check_api_key', methods=['POST'])
# def check_api_key():
#     data = request.get_json()
#     api_key = data.get('key')
#     if not api_key:
#         return jsonify({'error': 'API key is required'}), 400
#     conn = sqlite3.connect('api_keys.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
#     existing_key = cursor.fetchone()
#     conn.close()
#     if existing_key:
#         return jsonify({'valid': True, 'message': 'Key chính xác', 'ip': existing_key[1], 'key': existing_key[0]}), 200
#     else:
#         return jsonify({'valid': False, 'message': 'Key sai'}), 404

# @app.route('/delete_api_key', methods=['POST'])
# def delete_api_key():
#     data = request.get_json()
#     api_key = data.get('key')
#     if not api_key:
#         return jsonify({'error': 'API key is required'}), 400
#     conn = sqlite3.connect('api_keys.db')
#     cursor = conn.cursor()
#     cursor.execute('DELETE FROM api_keys WHERE api_key = ?', (api_key,))
#     conn.commit()
#     rows_deleted = cursor.rowcount
#     conn.close()
#     if rows_deleted > 0:
#         return jsonify({'message': 'API key deleted successfully'}), 200
#     else:
#         return jsonify({'error': 'API key not found'}), 404

# if __name__ == '__main__':
#     app.run(host='0.0.0.0',port=8000,debug=True)


from flask import Flask, jsonify, render_template_string, request
import base64
import string
import secrets
import time
import sqlite3

app = Flask(__name__)

def generate_random_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
random = generate_random_key()
def generate_api_key(ip, user_key):
    unique_string = f"{user_key}:{ip}"
    api_key = base64.b64encode(unique_string.encode()).decode()
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
    INSERT INTO api_keys (ip, api_key, timestamp)
    VALUES (?, ?, ?)
    ''', (ip, api_key, timestamp))
    conn.commit()
    conn.close()
    return api_key
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
        user_key = request.args.get('key')
        ip_param = request.remote_addr
        if not ip_param:
            return jsonify({'error': 'IP address not found'}), 500
        if not user_key:
            return jsonify({'error': 'User key is required'}), 400
        api_key = save_api_key(ip_param, user_key)
        url_to_shorten = f'https://kingnotngu.github.io/kingweb/?key={api_key}'
        return render_template_string(
            f"""
            <script>
                window.onload = function() {{
                    var url = "{url_to_shorten}";
                    window.location.replace(url);
                }};
            </script>
            """)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
@app.route('/generate_api_key2', methods=['GET'])
def generate_api_key_endpoint():
    try:
        user_key = request.args.get('key')
        ip_param = request.remote_addr
        if not ip_param:
            return jsonify({'error': 'IP address not found'}), 500
        if not user_key:
            return jsonify({'error': 'User key is required'}), 400
        api_key = save_api_key(ip_param, user_key)
        url_to_shorten = f'https://kingnotngu.github.io/kingweb/?key=?ug%20{api_key}'
        return render_template_string(
            f"""
            <script>
                window.onload = function() {{
                    var url = "{url_to_shorten}";
                    window.location.replace(url);
                }};
            </script>
            """)
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
@app.route('/check_api_key', methods=['POST'])
def check_api_key():
    data = request.get_json()
    api_key = data.get('key')
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    existing_key = cursor.fetchone()
    conn.close()
    
    if existing_key:
        return jsonify({'valid': True, 'message': 'Key is valid', 'ip': existing_key[1], 'key': existing_key[2]}), 200
    else:
        return jsonify({'valid': False, 'message': 'Key is invalid'}), 404 #, 'provided_key': api_key
@app.route('/delete_api_key', methods=['POST'])
def delete_api_key():
    data = request.get_json()
    api_key = data.get('key')
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM api_keys WHERE api_key = ?', (api_key,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    if rows_deleted > 0:
        return jsonify({'message': 'API key deleted successfully'}), 200
    else:
        return jsonify({'error': 'API key not found'}), 404
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    #app.run(debug=True)
