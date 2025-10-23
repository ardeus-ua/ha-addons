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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Дашборд Акумуляторів</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #ffffff;
                color: #212121;
                min-height: 100vh;
                padding: 20px;
                line-height: 1.5;
            }
            h1 {
                font-size: 2.5rem;
                font-weight: 500;
                text-align: center;
                margin-bottom: 2rem;
                color: #6200ee;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                padding: 0 1rem;
            }
            .battery-card {
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 1rem;
                text-align: center;
                transition: box-shadow 0.3s ease;
            }
            .battery-card:hover {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 0 6px 12px rgba(0, 0, 0, 0.2);
            }
            .battery {
                position: relative;
                width: 100%;
                height: 60px;
                border: 2px solid #757575;
                border-radius: 4px;
                background: #f5f5f5;
                overflow: hidden;
            }
            .battery-segments {
                display: flex;
                height: 100%;
                transition: all 0.5s ease;
            }
            .segment {
                flex: 1;
                border-right: 1px solid #e0e0e0;
            }
            .segment:last-child {
                border-right: none;
            }
            .battery-percentage {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 1.2rem;
                font-weight: 500;
                color: #212121;
                z-index: 1;
            }
            .battery-label {
                margin-top: 0.5rem;
                font-size: 1rem;
                color: #757575;
                text-transform: uppercase;
            }
            @media (max-width: 768px) {
                h1 {
                    font-size: 1.8rem;
                }
                .container {
                    grid-template-columns: 1fr;
                }
                .battery {
                    height: 50px;
                }
                .battery-percentage {
                    font-size: 1rem;
                }
                .battery-label {
                    font-size: 0.9rem;
                }
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('update_soc', (data) => {
                const cards = document.querySelectorAll('.battery-card');
                cards.forEach(card => {
                    const sn = card.dataset.sn;
                    const soc = data[sn] !== null ? data[sn] : 'N/A';
                    const percentage = card.querySelector('.battery-percentage');
                    const segments = card.querySelector('.battery-segments');
                    percentage.textContent = `${soc}%`;
                    segments.innerHTML = '';
                    for (let i = 0; i < 10; i++) {
                        const segment = document.createElement('div');
                        segment.className = 'segment';
                        segment.style.background = (i * 10) < soc ? (soc >= 50 ? '#4caf50' : (soc >= 20 ? '#ffca28' : '#f44336')) : '#f5f5f5';
                        segments.appendChild(segment);
                    }
                });
            });
        </script>
    </head>
    <body>
        <h1>Дашборд Акумуляторів</h1>
        <div class="container">
            {% for sn, name in sensors.items() %}
            <div class="battery-card" data-sn="{{ sn }}">
                <div class="battery">
                    <div class="battery-percentage">{{ data[sn] if data[sn] is not none else 'N/A' }}%</div>
                    <div class="battery-segments">
                        {% set soc = data[sn] if data[sn] is not none else 0 %}
                        {% for i in range(10) %}
                        <div class="segment" style="background: {{ '#4caf50' if soc >= 50 else ('#ffca28' if soc >= 20 else '#f44336') if (i * 10) < soc else '#f5f5f5' }};"></div>
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