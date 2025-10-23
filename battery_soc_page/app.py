from flask import Flask, request, jsonify, render_template_string
import json
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

DATA_FILE = '/app/data.json'
SENSORS = {
    "2407021154": "Ліфт п1",
    "2407024008": "Ліфт п2",
    "2407026195": "Ліфт п3",
    "2407026186": "Вода",
    "2407024187": "Опалення"
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
    # HTML template with Chart.js gauges
    html = """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>Дашборд Акумуляторів</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
            .gauge { width: 200px; height: 200px; margin: auto; }
            h1 { text-align: center; }
        </style>
    </head>
    <body>
        <h1>Стан Акумуляторів</h1>
        <div class="grid">
            {% for sn, name in sensors.items() %}
            <div>
                <canvas id="gauge_{{ sn }}" class="gauge"></canvas>
                <p style="text-align: center;">{{ name }}</p>
            </div>
            {% endfor %}
        </div>
        <script>
            const sensors = {{ sensors | tojson }};
            const data = {{ data | tojson }};
            Object.keys(sensors).forEach(sn => {
                const ctx = document.getElementById('gauge_' + sn).getContext('2d');
                const soc = data[sn] !== null ? data[sn] : 0;
                const color = soc >= 50 ? '#00cc00' : (soc >= 20 ? '#ffcc00' : '#cc0000');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [soc, 100 - soc],
                            backgroundColor: [color, '#e0e0e0'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        circumference: 180,
                        rotation: -90,
                        cutout: '70%',
                        plugins: {
                            legend: { display: false },
                            tooltip: { enabled: false },
                            title: {
                                display: true,
                                text: (data[sn] !== null ? data[sn] + '%' : 'N/A'),
                                position: 'bottom'
                            }
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html, sensors=SENSORS, data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)