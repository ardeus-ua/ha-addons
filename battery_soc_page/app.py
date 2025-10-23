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
        <meta charset="UTF-8">
        <title>Дашборд Акумуляторів</title>
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background: #000000 url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAJElEQVQIW2P8DwQMQwMDAz/ywIIGAwCDmBrAuQi+v8QzAAMAPr0AFm2y/7QAAAABJRU5ErkJggg==') repeat;
                margin: 0;
                padding: 20px;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                color: #e0e0e0;
                overflow: hidden;
            }
            h1 {
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                text-transform: uppercase;
                letter-spacing: 3px;
                margin-bottom: 30px;
                text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00;
                animation: fadeIn 1s ease-in;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .battery-row {
                display: flex;
                justify-content: center;
                gap: 40px;
                max-width: 1200px;
                flex-wrap: wrap;
            }
            .battery-container {
                text-align: center;
                perspective: 1000px;
            }
            .battery {
                position: relative;
                width: 250px;
                height: 80px;
                border: 4px solid #00ffff;
                border-radius: 15px;
                background: #111111;
                overflow: hidden;
                box-shadow: 0 0 15px #00ffff, inset 0 0 10px #000000;
                transition: transform 0.3s;
            }
            .battery-container:hover .battery {
                transform: rotateX(5deg) scale(1.05);
            }
            .battery-segments {
                display: flex;
                height: 100%;
                transition: all 0.5s ease;
            }
            .segment {
                flex: 1;
                border-right: 2px solid #333;
            }
            .segment:last-child {
                border-right: none;
            }
            .battery-percentage {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 5px #000000, 0 0 10px #00ff00;
                z-index: 1;
                transition: color 0.3s;
            }
            .battery-container:hover .battery-percentage {
                color: #00ff00;
            }
            .battery-label {
                margin-top: 15px;
                font-size: 18px;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 0 0 5px #00ff00;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('update_soc', (data) => {
                const containers = document.querySelectorAll('.battery-container');
                containers.forEach(container => {
                    const sn = container.dataset.sn;
                    const soc = data[sn] !== null ? data[sn] : 'N/A';
                    const percentage = container.querySelector('.battery-percentage');
                    const segments = container.querySelector('.battery-segments');
                    percentage.textContent = `${soc}%`;
                    segments.innerHTML = '';
                    for (let i = 0; i < 10; i++) {
                        const segment = document.createElement('div');
                        segment.className = 'segment';
                        segment.style.background = (i * 10) < soc ? (soc >= 50 ? '#00ff00' : (soc >= 20 ? '#ffff00' : '#ff0000')) : '#111111';
                        segments.appendChild(segment);
                    }
                });
            });
        </script>
    </head>
    <body>
        <h1>Дашборд Акумуляторів</h1>
        <div class="battery-row">
            {% for sn, name in sensors.items() %}
            <div class="battery-container" data-sn="{{ sn }}">
                <div class="battery">
                    <div class="battery-percentage">{{ data[sn] if data[sn] is not none else 'N/A' }}%</div>
                    <div class="battery-segments">
                        {% set soc = data[sn] if data[sn] is not none else 0 %}
                        {% for i in range(10) %}
                        <div class="segment" style="background: {{ '#00ff00' if soc >= 50 else ('#ffff00' if soc >= 20 else '#ff0000') if (i * 10) < soc else '#111111' }};"></div>
                        {% endfor %}
                    </div>
                </div>
                <p class="battery-label">{{ name }}</p>
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