import json
import os
import socket
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'messages.json')

def load_messages():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_messages(messages):
    with open(DATA_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

def get_nickname(ip_address):
    # 1. Try to resolve hostname
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        if hostname:
            return hostname
    except Exception:
        pass
        
    # 2. Fallback to IP
    return ip_address

@app.route('/', methods=['GET'])
def index():
    messages = load_messages()
    # Sort by timestamp descending (newest first)
    messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return render_template('index.html', messages=messages)

@app.route('/add', methods=['POST'])
def add_message():
    content = request.form.get('content')
    if content:
        ip = request.remote_addr
        messages = load_messages()
        new_msg = {
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'id': int(datetime.now().timestamp() * 1000),
            'ip': ip,
            'nickname': get_nickname(ip)
        }
        messages.append(new_msg)
        save_messages(messages)
    return redirect(url_for('index'))

def get_lan_ip():
    """Attempt to find the primary LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.before_request
def redirect_localhost():
    """Redirect localhost/127.0.0.1 to LAN IP."""
    # Avoid redirect loops if LAN IP is somehow 127.0.0.1 (unlikely but safe)
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        lan_ip = get_lan_ip()
        if lan_ip != '127.0.0.1':
            # Reconstruct the URL with the new host
            new_url = request.url.replace(request.host, f"{lan_ip}:5000")
            return redirect(new_url)

@app.route('/updates')
def updates():
    since_id = request.args.get('since_id', 0, type=int)
    want_json = request.args.get('json')
    
    messages = load_messages()
    # Filter for new messages only
    new_messages = [m for m in messages if m['id'] > since_id]
    # Sort by timestamp descending (newest first)
    new_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    if want_json:
        return new_messages

    # We return a partial HTML snippet. Flask can render a loop without a full page wrapper.
    return render_template('updates.html', messages=new_messages)

if __name__ == '__main__':
    # Host 0.0.0.0 is crucial for local network access
    app.run(host='0.0.0.0', port=5000, debug=True)
