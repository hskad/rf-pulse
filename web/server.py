"""
RF-Pulse: Local Web Dashboard & Telemetry API Server
Serves the web UI and provides JSON endpoints for Parquet telemetry,
on-demand probe collection, and AI diagnostic ticket generation.
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import urllib.parse
import pandas as pd
from models.diagnostics import (
    compute_physical_attenuation,
    load_telemetry,
    train_link_health_classifier,
    generate_cc_dispatch_ticket,
    fit_physical_path_loss_model
)

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class RFPulseHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/telemetry":
            self.handle_api_telemetry()
        elif parsed.path == "/api/diagnostics":
            self.handle_api_diagnostics()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/collect":
            self.handle_api_collect()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_api_telemetry(self):
        parquet_path = "data/rf_pulse_dataset.parquet"
        if not os.path.exists(parquet_path):
            self.respond_json({"error": "No telemetry dataset found"}, status=404)
            return

        df = pd.read_parquet(parquet_path)
        # Convert timestamp to ISO string for JSON serialization
        df_copy = df.copy()
        df_copy["timestamp"] = df_copy["timestamp"].astype(str)
        records = df_copy.to_dict(orient="records")

        real_count = int((df["is_synthetic"] == False).sum())
        synth_count = int((df["is_synthetic"] == True).sum())

        response = {
            "total_rows": len(df),
            "real_count": real_count,
            "synthetic_count": synth_count,
            "records": records
        }
        self.respond_json(response)

    def handle_api_diagnostics(self):
        parquet_path = "data/rf_pulse_dataset.parquet"
        if not os.path.exists(parquet_path):
            self.respond_json({"error": "No telemetry dataset found"}, status=404)
            return

        df = pd.read_parquet(parquet_path)
        physical_summary = compute_physical_attenuation(df)
        path_loss_summary = fit_physical_path_loss_model(df)
        clf, analyzed_df, classes = train_link_health_classifier(df)
        state_distribution = analyzed_df["predicted_state"].value_counts().to_dict()
        ticket_text = generate_cc_dispatch_ticket(analyzed_df, physical_summary, path_loss_summary)

        # Sanitize ticket formatting (clean plain web text)
        clean_ticket = ticket_text.replace("[bold cyan]", "").replace("[/bold cyan]", "")
        clean_ticket = clean_ticket.replace("[yellow]", "").replace("[/yellow]", "")
        clean_ticket = clean_ticket.replace("[dim]", "").replace("[/dim]", "")
        clean_ticket = clean_ticket.replace("[bold green]", "").replace("[/bold green]", "")
        clean_ticket = clean_ticket.replace("[bold magenta]", "").replace("[/bold magenta]", "")

        # Select an active observation from real physical measurements to refresh stats dynamically
        real_df = df[df["is_synthetic"] == False]
        sample_obs = real_df.sample(1).iloc[0] if not real_df.empty else df.iloc[-1]

        response = {
            "physical_decomposition": physical_summary,
            "path_loss": path_loss_summary,
            "health_distribution": state_distribution,
            "ticket": clean_ticket.strip(),
            "latest_metrics": {
                "bssid": str(sample_obs.get("bssid", "Unknown")),
                "ssid": str(sample_obs.get("ssid", "R04-5B4A")),
                "band_ghz": float(sample_obs.get("band_ghz", 2.4)),
                "channel": int(sample_obs.get("channel", 13)),
                "rssi_dbm": float(sample_obs["rssi_dbm"]),
                "tx_rate_mbps": float(sample_obs["tx_rate_mbps"]),
                "ping_rtt_avg_ms": float(sample_obs["ping_rtt_avg_ms"]),
                "ping_jitter_ms": float(sample_obs["ping_jitter_ms"]),
                "packet_loss_pct": float(sample_obs["packet_loss_pct"]),
                "location_tag": str(sample_obs["location_tag"]),
                "door_state": str(sample_obs["door_state"])
            }
        }
        self.respond_json(response)

    def handle_api_collect(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        body = json.loads(post_data) if post_data else {}

        loc = body.get("location", "Desk")
        door = body.get("door", "Open")
        samples = int(body.get("samples", 3))

        cmd = [sys.executable, "-m", "collector.probe", "--location", loc, "--door", door, "--samples", str(samples), "--interval", "1"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            self.respond_json({"status": "success", "message": f"Collected {samples} samples for {loc} ({door})"})
        else:
            self.respond_json({"status": "error", "error": result.stderr or result.stdout}, status=500)

    def respond_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run():
    with socketserver.TCPServer(("", PORT), RFPulseHandler) as httpd:
        print(f"[*] RF-Pulse Live Dashboard running at http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run()
