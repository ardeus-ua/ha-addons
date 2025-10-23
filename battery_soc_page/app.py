from flask import Flask, request, jsonify, render_template_string
import json
import os
import logging

app = Flask(__name__)
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
                background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
                margin: 0;
                padding: 20px;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                color: #d3d3d3;
            }
            h1 {
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 20px;
                text-shadow: 0 0 5px #00ff00;
            }
            .battery-row {
                display: flex;
                justify-content: center;
                gap: 30px;
                max-width: 1000px;
                flex-wrap: wrap;
            }
            .battery-container {
                text-align: center;
            }
            .battery {
                position: relative;
                width: 200px;
                height: 60px;
                border: 3px solid #00ffff;
                border-radius: 10px;
                background: #333333;
                overflow: hidden;
                box-shadow: 0 0 10px #00ffff;
            }
            .battery-segments {
                display: flex;
                height: 100%;
                transition: all 0.3s ease;
            }
            .segment {
                flex: 1;
                border-right: 1px solid #555;
            }
            .segment:last-child {
                border-right: none;
            }
            .battery-percentage {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 3px #000000;
                z-index: 1;
            }
            .battery-label {
                margin-top: 10px;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        </style>
    </head>
    <body>
        <h1>Стан Акумуляторів</h1>
        <div class="battery-row">
            {% for sn, name in sensors.items() %}
            <div class="battery-container">
                <div class="battery">
                    <div class="battery-percentage">{{ data[sn] if data[sn] is not none else 'N/A' }}%</div>
                    <div class="battery-segments">
                        {% set soc = data[sn] if data[sn] is not none else 0 %}
                        {% for i in range(10) %}
                        <div class="segment" style="background: {{ '#00ff00' if soc >= 50 else ('#ffff00' if soc >= 20 else '#ff0000') if (i * 10) < soc else '#333333' }};"></div>
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)