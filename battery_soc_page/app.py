from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO
import json
import os
import logging
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Замени на уникальный ключ
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

DATA_FILE = '/app/data.json'
SENSORS = {
    "1": "Ліфт п1",
    "2": "Ліфт п2",
    "3": "Ліфт п3",
    "4": "Вода",
    "5": "Опалення"
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {sn: None for sn in SENSORS}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

data = load_data()

@app.route('/api/battery_soc', methods=['POST'])
def update_battery_soc():
    try:
        new_data = request.get_json()
        app.logger.debug(f"Received data: {new_data}")
        for sn, soc in new_data.items():
            if sn in SENSORS:
                data[sn] = soc
        save_data(data)
        socketio.emit('update_soc', data)
        return jsonify({"status": "ok"})
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/', methods=['GET'])
def index():
    html = """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Індикатори Енергосистеми</title>
        <style>
            :root {
                --primary-color: #007bff;
                --success-color: #5cb85c;
                --warning-color: #f0ad4e;
                --danger-color: #d9534f;
                --bg-color: #f8f9fa;
                --card-bg: #ffffff;
                --text-color: #333;
            }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: flex-start; 
                min-height: 100vh; 
                margin: 0; 
                padding: 20px 10px;
                background-color: var(--bg-color); 
                color: var(--text-color);
            }
            h1 { 
                margin-bottom: 30px; 
                font-size: 1.2em;
                text-align: center;
            }
            .battery-grid { 
                display: flex; 
                gap: 20px; 
                flex-wrap: wrap; 
                justify-content: center;
                width: 100%;
                max-width: 1200px;
            }
            .indicator-unit { 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                padding: 20px; 
                border: 1px solid #e0e0e0; 
                border-radius: 12px; 
                background: var(--card-bg); 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
                transition: transform 0.2s;
                width: calc(20% - 20px); 
                min-width: 180px;
                box-sizing: border-box;
            }
            .indicator-unit:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 15px rgba(0,0,0,0.1);
            }
            .system-title {
                font-size: 1.2em;
                margin-bottom: 15px;
                font-weight: 600;
            }
            .battery-container { 
                width: 100px; 
                height: 60px; 
                border: 3px solid var(--text-color); 
                border-radius: 8px; 
                position: relative; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                margin-top: 10px; 
                background-color: #f0f0f0; 
                overflow: hidden;
            }
            .battery-container::after { 
                content: ''; 
                position: absolute; 
                right: -8px; 
                top: 50%; 
                transform: translateY(-50%); 
                width: 6px; 
                height: 15px; 
                background-color: var(--text-color); 
                border-radius: 0 3px 3px 0; 
            }
            .battery-segments {
                display: flex;
                height: 100%;
                width: 100%;
                position: absolute;
                top: 0;
                left: 0;
            }
            .segment {
                flex: 1;
                border-right: 1px solid #e0e0e0;
            }
            .segment:last-child {
                border-right: none;
            }
            .battery-level { 
                font-size: 2em;
                font-weight: bold; 
                color: var(--text-color); 
                transition: color 0.3s;
                position: relative;
                z-index: 1;
            }
            .timestamp-text { 
                margin-top: 15px; 
                font-size: 0.8em; 
                color: #777; 
                text-align: center; 
            }
            /* Кольорові класи для сегментів */
            .color-success { background-color: var(--success-color) !important; }
            .color-warning { background-color: var(--warning-color) !important; }
            .color-danger { background-color: var(--danger-color) !important; }
            /* Адаптивність */
            @media (max-width: 1024px) {
                .indicator-unit {
                    width: calc(33.33% - 20px);
                }
            }
            @media (max-width: 768px) {
                .indicator-unit {
                    width: calc(50% - 15px);
                }
            }
            @media (max-width: 500px) {
                .indicator-unit {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('update_soc', (data) => {
                const units = document.querySelectorAll('.indicator-unit');
                units.forEach(unit => {
                    const sn = unit.dataset.sn;
                    const soc = data[sn] !== null ? data[sn] : 'N/A';
                    const level = unit.querySelector('.battery-level');
                    const segments = unit.querySelector('.battery-segments');
                    level.textContent = `${soc}%`;
                    level.className = 'battery-level ' + (soc >= 50 ? 'color-success' : (soc >= 20 ? 'color-warning' : 'color-danger'));
                    segments.innerHTML = '';
                    for (let i = 0; i < 10; i++) {
                        const segment = document.createElement('div');
                        segment.className = 'segment';
                        segment.classList.add(soc >= 50 ? 'color-success' : (soc >= 20 ? 'color-warning' : 'color-danger'));
                        if ((i * 10) >= soc) segment.classList.remove('color-success', 'color-warning', 'color-danger');
                        segments.appendChild(segment);
                    }
                });
            });
        </script>
    </head>
    <body>
        <h1>Індикатори Енергосистеми</h1>
        <div class="battery-grid">
            {% for sn, name in sensors.items() %}
            <div class="indicator-unit" data-sn="{{ sn }}">
                <div class="system-title">{{ name }}</div>
                <div class="battery-container">
                    <div class="battery-level {{ data[sn] if data[sn] is not none else 'N/A' >= 50 and 'color-success' or data[sn] >= 20 and 'color-warning' or 'color-danger' }}">{{ data[sn] if data[sn] is not none else 'N/A' }}%</div>
                    <div class="battery-segments">
                        {% set soc = data[sn] if data[sn] is not none else 0 %}
                        {% for i in range(10) %}
                        <div class="segment {{ '#5cb85c' if soc >= 50 else ('#f0ad4e' if soc >= 20 else '#d9534f') if (i * 10) < soc else '' }}"></div>
                        {% endfor %}
                    </div>
                </div>
                <div class="timestamp-text">Оновлено: {{ time.strftime('%H:%M:%S') }}</div>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, sensors=SENSORS, data=data)

def send_updates():
    while True:
        socketio.emit('update_soc', data)
        time.sleep(5)

if __name__ == '__main__':
    import threading
    update_thread = threading.Thread(target=send_updates, daemon=True)
    update_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000)