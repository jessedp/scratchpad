import json
import os
import socket
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'messages.json')
NAS_HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'nas_history.jsonl')

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

def load_nas_history():
    if not os.path.exists(NAS_HISTORY_FILE):
        return []
    history = []
    try:
        with open(NAS_HISTORY_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
    except (json.JSONDecodeError, IOError):
        pass
    return history

def get_nickname(ip_address):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        if hostname:
            return hostname
    except Exception:
        pass
    return ip_address

@app.route('/', methods=['GET'])
def index():
    messages = load_messages()
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

@app.route('/nas-report')
def nas_report():
    history = load_nas_history()
    if not history:
        return {"error": "No NAS data available"} if request.args.get('json') else "No NAS data available yet."

    latest = history[-1]
    
    if request.args.get('json'):
        # Use disk used as the total if available, otherwise sum top-level dirs
        json_total = latest.get('disk', {}).get('used', sum(v for k, v in latest['dirs'].items() if '/' not in k))
        return {
            "media": latest['dirs'].get('media', 0),
            "total": json_total,
            "disk": latest.get('disk', {})
        }

    # Drill-down logic
    target_dir = request.args.get('dir', '').strip('/')
    
    def is_child(path, parent):
        if not parent:
            return '/' not in path
        if not path.startswith(parent + '/'):
            return False
        child_part = path[len(parent)+1:]
        return '/' not in child_part

    if target_dir:
        filtered_dirs = [d for d in latest['dirs'].keys() if is_child(d, target_dir)]
        # If we have no data for this specific sub-dir, it might be a depth issue
        # but for now we'll just show what we found.
    else:
        filtered_dirs = [d for d in latest['dirs'].keys() if '/' not in d]

    sorted_dirs = sorted(filtered_dirs)
    
    return render_template('nas_report.html', 
                           history=history, 
                           latest=latest, 
                           dirs=sorted_dirs, 
                           current_dir=target_dir)

@app.route('/updates')
def updates():
    since_id = request.args.get('since_id', 0, type=int)
    want_json = request.args.get('json')
    messages = load_messages()
    new_messages = [m for m in messages if m['id'] > since_id]
    new_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    if want_json:
        return new_messages
    return render_template('updates.html', messages=new_messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
