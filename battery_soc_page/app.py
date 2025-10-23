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
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                padding: 20px;
                margin: 0;
            }
            h1 {
                text-align: center;
                color: #333;
            }
            .battery-row {
                display: flex;
                justify-content: center;
                gap: 20px;
                max-width: 1000px;
                margin: 0 auto;
            }
            .battery-container {
                text-align: center;
            }
            .battery {
                position: relative;
                width: 150px;
                height: 50px;
                border: 2px solid #333;
                border-radius: 5px;
                background: #e0e0e0;
                overflow: hidden;
            }
            .battery-segments {
                display: flex;
                height: 100%;
            }
            .segment {
                flex: 1;
                border-right: 1px solid #fff;
            }
            .segment:last-child {
                border-right: none;
            }
            .battery-percentage {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 16px;
                font-weight: bold;
                color: #333;
                text-shadow: 1px 1px 1px #fff;
                z-index: 1;
            }
            .battery-label {
                margin-top: 5px;
                font-size: 14px;
                color: #333;
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
                        <div class="segment" style="background: {{ '#00cc00' if soc >= 50 else ('#ffcc00' if soc >= 20 else '#cc0000') if (i * 10) < soc else '#e0e0e0' }};"></div>
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