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

        response = {
            "physical_decomposition": physical_summary,
            "path_loss": path_loss_summary,
            "health_distribution": state_distribution,
            "ticket": clean_ticket.strip(),
            "latest_metrics": {
                "bssid": str(df["bssid"].dropna().iloc[-1]) if not df["bssid"].dropna().empty else "Unknown",
                "ssid": str(df["ssid"].dropna().iloc[-1]) if not df["ssid"].dropna().empty else "Unknown",
                "band_ghz": float(df["band_ghz"].dropna().iloc[-1]) if not df["band_ghz"].dropna().empty else 2.4,
                "channel": int(df["channel"].dropna().iloc[-1]) if not df["channel"].dropna().empty else 1,
                "rssi_dbm": float(df["rssi_dbm"].dropna().iloc[-1]) if not df["rssi_dbm"].dropna().empty else -70.0,
                "tx_rate_mbps": float(df["tx_rate_mbps"].dropna().iloc[-1]) if not df["tx_rate_mbps"].dropna().empty else 0.0,
                "ping_rtt_avg_ms": float(df["ping_rtt_avg_ms"].dropna().iloc[-1]) if not df["ping_rtt_avg_ms"].dropna().empty else 0.0,
                "ping_jitter_ms": float(df["ping_jitter_ms"].dropna().iloc[-1]) if not df["ping_jitter_ms"].dropna().empty else 0.0,
                "packet_loss_pct": float(df["packet_loss_pct"].dropna().iloc[-1]) if not df["packet_loss_pct"].dropna().empty else 0.0
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
