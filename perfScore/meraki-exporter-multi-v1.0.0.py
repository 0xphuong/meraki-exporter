import os
import requests
import time
from prometheus_client import CollectorRegistry, Gauge, generate_latest

# ENV
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
API_BASE_URL = 'https://api.meraki.com/api/v1/devices'
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY
}

# Custom registry
registry = CollectorRegistry()

# Get metric from meraki
def get_serials():
    serials = {}
    for key, value in os.environ.items():
        if key.startswith('SERIAL_'):
            name = key[7:].lower()  # Get name from 'SERIAL_'
            serials[name] = value
    return serials

# Init Gauge metrics for serial
serials = get_serials()
perf_score = Gauge('meraki_performance', 'Performance score of Meraki device', ['device'], registry=registry)

def fetch_meraki_data(serial):
    try:
        url = f'{API_BASE_URL}/{serial}/appliance/performance'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['perfScore']
    except requests.RequestException as e:
        print(f"Error fetching data for {serial}: {e}")
        return None

def update_metrics():
    for name, serial in serials.items():
        score = fetch_meraki_data(serial)
        if score is not None:
            perf_score.labels(device=name).set(score)
            print(f"Updated performance score for {name}: {score}")
    return generate_latest(registry)

if __name__ == '__main__':
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/metrics':
                metrics = update_metrics()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(metrics)
            else:
                self.send_error(404, 'Not Found')

        def log_message(self, format, *args):
            print(f"{self.client_address[0]} - - [{self.log_date_time_string()}] {format%args}")

    httpd = HTTPServer(('', 8000), MetricsHandler)
    print("Prometheus metrics server started on port 8000")
    print(f"Monitoring devices: {', '.join(serials.keys())}")
    httpd.serve_forever()