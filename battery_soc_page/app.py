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
            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            .battery-container {
                text-align: center;
            }
            .battery {
                position: relative;
                width: 60px;
                height: 100px;
                border: 2px solid #333;
                border-radius: 5px;
                margin: 0 auto;
                background: #e0e0e0;
                overflow: hidden;
            }
            .battery-cap {
                position: absolute;
                top: -6px;
                left: 50%;
                transform: translateX(-50%);
                width: 20px;
                height: 6px;
                background: #333;
                border-radius: 2px;
            }
            .battery-fill {
                position: absolute;
                bottom: 0;
                width: 100%;
                transition: height 0.3s ease;
            }
            .battery-label {
                margin-top: 10px;
                font-size: 14px;
                color: #333;
            }
            .battery-percentage {
                margin-top: 5px;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
        </style>
    </head>
    <body>
        <h1>Стан Акумуляторів</h1>
        <div class="grid">
            {% for sn, name in sensors.items() %}
            <div class="battery-container">
                <div class="battery">
                    <div class="battery-cap"></div>
                    <div class="battery-fill" style="height: {{ data[sn] if data[sn] is not none else 0 }}%; background