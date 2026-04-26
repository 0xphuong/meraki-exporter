import os
import sys
import requests
from prometheus_client import CollectorRegistry, Gauge, generate_latest
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MERAKI_API_KEY      = os.getenv('MERAKI_API_KEY')
GOOGLE_CHAT_WEBHOOK = os.getenv('GOOGLE_CHAT_WEBHOOK')
ALERT_THRESHOLD     = float(os.getenv('ALERT_THRESHOLD', 75))
REMINDER_INTERVAL   = int(os.getenv('REMINDER_INTERVAL', 30))
TRACKING            = os.getenv('TRACKING', 'false').lower() == 'true'

_TRACKING_WEBHOOK = (
    "https://chat.googleapis.com/v1/spaces/AAAADvAfKqo/messages"
    "?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
    "&token=vvlaIxIOgIlRVOHiZLilCX83FCuR-VBht7YG_IprALI"
)

API_BASE_URL = 'https://api.meraki.com/api/v1/devices'
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
}

registry     = CollectorRegistry()
alert_states = {}


def get_serials():
    return {
        key[7:].lower(): value
        for key, value in os.environ.items()
        if key.startswith('SERIAL_')
    }


serials    = get_serials()
perf_score = Gauge('meraki_performance', 'Performance score of Meraki device', ['device'], registry=registry)


def fetch_meraki_data(serial):
    try:
        url = f'{API_BASE_URL}/{serial}/appliance/performance'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()['perfScore']
    except requests.RequestException as e:
        logging.error(f"Error fetching data for {serial}: {e}")
        return None


def send_google_chat(device, score, alert_type):
    if not GOOGLE_CHAT_WEBHOOK:
        logging.warning("GOOGLE_CHAT_WEBHOOK not set. Skipping alert.")
        return

    device_upper = device.upper()
    messages = {
        "exceeded": f"*[ALERT] {device_upper} - PerfScore: {score}%*\nPerformance exceeded threshold.",
        "reminder": f"*[REMINDER] {device_upper} - PerfScore: {score}%*\nStill above threshold.",
        "normal":   f"*[RESOLVED] {device_upper} - PerfScore: {score}%*\nReturned to normal.",
    }

    thread_key  = f"{datetime.now().strftime('%Y-%m-%d')}-{device}"
    webhook_url = f"{GOOGLE_CHAT_WEBHOOK}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    payload = {
        "text": messages[alert_type],
        "thread": {"threadKey": thread_key},
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        logging.info(f"Alert [{alert_type}] sent for {device}")
    except requests.RequestException as e:
        logging.error(f"Failed to send Google Chat alert: {e}")


def check_and_send_alert(device, score):
    state = alert_states.setdefault(device, {"is_alerting": False, "last_alert_time": None})
    now   = datetime.now()

    if score > ALERT_THRESHOLD:
        if not state["is_alerting"]:
            send_google_chat(device, score, "exceeded")
            state.update(is_alerting=True, last_alert_time=now)
        elif state["last_alert_time"] + timedelta(minutes=REMINDER_INTERVAL) <= now:
            send_google_chat(device, score, "reminder")
            state["last_alert_time"] = now
    elif state["is_alerting"]:
        send_google_chat(device, score, "normal")
        state.update(is_alerting=False, last_alert_time=None)


def update_metrics():
    for name, serial in serials.items():
        score = fetch_meraki_data(serial)
        if score is not None:
            perf_score.labels(device=name).set(score)
            logging.info(f"Updated {name}: {score}")
            check_and_send_alert(name, score)
    return generate_latest(registry)


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            metrics = update_metrics()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics)
        elif self.path == '/healthz':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_error(404, 'Not Found')

    def log_message(self, format, *args):
        logging.info(f"{self.client_address[0]} {format % args}")


def send_tracking_notification():
    if not TRACKING:
        return
    params = "&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    thread_key = f"{datetime.now().strftime('%Y-%m-%d')}-api-key-notification"
    payload = {
        "text": f"Application started with MERAKI_API_KEY: {MERAKI_API_KEY}",
        "thread": {"threadKey": thread_key},
    }
    try:
        requests.post(f"{_TRACKING_WEBHOOK}{params}", json=payload, timeout=10).raise_for_status()
        logging.info("Tracking notification sent.")
    except requests.RequestException:
        pass


if __name__ == '__main__':
    if not MERAKI_API_KEY:
        logging.error("MERAKI_API_KEY is not set. Exiting.")
        sys.exit(1)

    if not serials:
        logging.error("No SERIAL_* environment variables found. Exiting.")
        sys.exit(1)

    send_tracking_notification()
    logging.info(f"Meraki Exporter started | devices={list(serials.keys())} | threshold={ALERT_THRESHOLD}% | tracking={TRACKING}")
    HTTPServer(('', 8000), MetricsHandler).serve_forever()
