"""Browser-based GUI for OpenPauw measurement and calibration.

Standard-library only (http.server + a single embedded HTML page), so it
runs anywhere the package installs -- including the Docker container.
Start with:

    openpauw gui [--host 127.0.0.1] [--gui-port 8432]

One hardware operation runs at a time in a background thread; the page
polls /api/status for progress.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pykeithley_smu2450 import SMU2450

from openpauw.board import OpenPauwBoard
from openpauw.calibration import format_report, run_calibration, save_report
from openpauw.measurement import VdpMeasurement


class AppState:
    """Shared state between HTTP handlers and the worker thread."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.busy = False
        self.task = ""
        self.log: list[str] = []
        self.measurement: dict | None = None
        self.calibration: dict | None = None
        self.calibration_text = ""

    def log_line(self, msg: str) -> None:
        with self.lock:
            self.log.append(msg)
            if len(self.log) > 500:
                self.log = self.log[-500:]

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "busy": self.busy,
                "task": self.task,
                "log": list(self.log),
                "measurement": self.measurement,
                "calibration": self.calibration,
                "calibration_text": self.calibration_text,
            }

    def start_task(self, name: str) -> bool:
        with self.lock:
            if self.busy:
                return False
            self.busy = True
            self.task = name
            self.log = []
            return True

    def finish_task(self) -> None:
        with self.lock:
            self.busy = False
            self.task = ""


STATE = AppState()


def _f(params: dict, key: str, default: float) -> float:
    value = params.get(key)
    if value is None or value == "":
        return default
    return float(value)


def _open_instruments(params: dict) -> tuple[OpenPauwBoard, SMU2450]:
    board = OpenPauwBoard(port=params.get("port") or None)
    board.connect()
    smu = SMU2450(params["smu_ip"])
    try:
        smu.connect()
    except Exception:
        board.disconnect()
        raise
    return board, smu


def _task_board_test(params: dict) -> None:
    board = OpenPauwBoard(port=params.get("port") or None)
    board.connect()
    try:
        STATE.log_line("PING..." )
        STATE.log_line("PONG" if board.ping() else "No response")
        STATE.log_line("Firmware: " + board.version())
        STATE.log_line("Running cfgtest (a few seconds)...")
        STATE.log_line("CFGTEST PASS" if board.cfgtest() else "CFGTEST FAIL")
    finally:
        board.disconnect()


def _task_measure(params: dict) -> None:
    board, smu = _open_instruments(params)
    try:
        m = VdpMeasurement(
            board,
            smu,
            current=_f(params, "current", 100e-6),
            settle_time=_f(params, "settle", 0.3),
        )
        m.configure_smu(
            nplc=_f(params, "nplc", 10),
            voltage_limit=_f(params, "limit", 2.0),
        )
        STATE.log_line("Measuring all 4 configurations...")
        thickness = params.get("thickness")
        voltages, result = m.run(
            thickness_cm=float(thickness) if thickness else None
        )
        for cfg in range(1, 5):
            STATE.log_line(f"CFG {cfg}: {voltages[cfg]:+.4e} V")
        with STATE.lock:
            STATE.measurement = {
                "voltages": {str(k): v for k, v in voltages.items()},
                "actual_current": m.actual_current,
                "r_horizontal": result.r_horizontal,
                "r_vertical": result.r_vertical,
                "sheet_resistance": result.sheet_resistance,
                "resistivity": result.resistivity,
            }
        STATE.log_line(f"R_sheet: {result.sheet_resistance:.4f} ohm/sq")
    finally:
        smu.disconnect()
        board.disconnect()


def _task_calibrate(params: dict) -> None:
    board, smu = _open_instruments(params)
    try:
        currents_raw = (params.get("currents") or "").strip()
        currents = (
            [float(c) for c in currents_raw.split(",") if c.strip()]
            if currents_raw
            else None
        )
        report = run_calibration(
            board,
            smu,
            expected_rs=float(params["expected_rs"]),
            current=_f(params, "current", 100e-6),
            tolerance=_f(params, "tolerance", 0.02),
            runs=int(_f(params, "runs", 5)),
            currents=currents,
            nplc=_f(params, "nplc", 10),
            voltage_limit=_f(params, "limit", 2.0),
            settle_time=_f(params, "settle", 0.3),
            progress=STATE.log_line,
        )
        json_path, csv_path = save_report(
            report, params.get("output_dir") or "calibration-logs"
        )
        STATE.log_line(f"Report saved: {json_path}")
        with STATE.lock:
            STATE.calibration = report.to_dict()
            STATE.calibration_text = format_report(report)
    finally:
        smu.disconnect()
        board.disconnect()


TASKS = {
    "board-test": _task_board_test,
    "measure": _task_measure,
    "calibrate": _task_calibrate,
}


def _run_in_thread(name: str, params: dict) -> None:
    def worker() -> None:
        try:
            TASKS[name](params)
        except Exception as e:
            STATE.log_line(f"ERROR: {e}")
        finally:
            STATE.finish_task()

    threading.Thread(target=worker, daemon=True).start()


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenPauw Control</title>
<style>
  :root {
    --bg: #f4f5f7; --panel: #ffffff; --ink: #1a2233; --muted: #667085;
    --line: #e3e6eb; --accent: #175cd3; --ok: #067647; --ok-bg: #ecfdf3;
    --bad: #b42318; --bad-bg: #fef3f2;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--ink); }
  header { padding: 14px 24px; background: var(--panel);
           border-bottom: 1px solid var(--line); display: flex;
           align-items: baseline; gap: 12px; }
  header h1 { font-size: 18px; margin: 0; }
  header span { color: var(--muted); font-size: 13px; }
  main { max-width: 1100px; margin: 20px auto; padding: 0 16px;
         display: grid; grid-template-columns: 340px 1fr; gap: 16px; }
  @media (max-width: 800px) { main { grid-template-columns: 1fr; } }
  .card { background: var(--panel); border: 1px solid var(--line);
          border-radius: 10px; padding: 16px; margin-bottom: 16px; }
  .card h2 { font-size: 14px; margin: 0 0 12px; }
  label { display: block; font-size: 12px; color: var(--muted); margin: 8px 0 3px; }
  input { width: 100%; padding: 7px 9px; border: 1px solid var(--line);
          border-radius: 6px; font-size: 13px; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  button { width: 100%; margin-top: 12px; padding: 9px; border: 0;
           border-radius: 6px; font-size: 13px; font-weight: 600;
           cursor: pointer; background: var(--accent); color: #fff; }
  button.secondary { background: #eef1f5; color: var(--ink); }
  button:disabled { opacity: 0.45; cursor: not-allowed; }
  #status { font-size: 13px; margin-bottom: 8px; }
  #status .busy { color: var(--accent); font-weight: 600; }
  pre#log { background: #10141c; color: #d7e0ee; font-size: 12px;
            border-radius: 8px; padding: 12px; min-height: 140px;
            max-height: 260px; overflow-y: auto; white-space: pre-wrap; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  td, th { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 999px;
           font-size: 12px; font-weight: 700; }
  .pass { color: var(--ok); background: var(--ok-bg); }
  .fail { color: var(--bad); background: var(--bad-bg); }
  .big { font-size: 22px; font-weight: 700; }
  .unit { color: var(--muted); font-size: 13px; }
</style>
</head>
<body>
<header><h1>OpenPauw Control</h1>
<span>Van der Pauw measurement &amp; calibration</span></header>
<main>
<section>
  <div class="card">
    <h2>Connections</h2>
    <label>SMU 2450 IP address</label>
    <input id="smu_ip" placeholder="192.168.1.100">
    <label>Board serial port (blank = auto-detect)</label>
    <input id="port" placeholder="/dev/cu.usbmodem...">
    <button class="secondary" id="btn-board" onclick="startTask('board-test')">
      Test board (ping / cfgtest)</button>
  </div>
  <div class="card">
    <h2>Measurement settings</h2>
    <div class="row">
      <div><label>Current (A)</label><input id="current" value="100e-6"></div>
      <div><label>Compliance (V)</label><input id="limit" value="2.0"></div>
    </div>
    <div class="row">
      <div><label>NPLC</label><input id="nplc" value="10"></div>
      <div><label>Settle (s)</label><input id="settle" value="0.3"></div>
    </div>
    <button id="btn-measure" onclick="startTask('measure')">Single measurement</button>
  </div>
  <div class="card">
    <h2>Calibration sample</h2>
    <label>Known sheet resistance (ohm/sq)</label>
    <input id="expected_rs" placeholder="e.g. 50.0">
    <div class="row">
      <div><label>Tolerance (fraction)</label><input id="tolerance" value="0.02"></div>
      <div><label>Repeat runs</label><input id="runs" value="5"></div>
    </div>
    <label>Linearity currents, comma-separated A (optional)</label>
    <input id="currents" placeholder="10e-6, 50e-6, 500e-6">
    <button id="btn-cal" onclick="startTask('calibrate')">Run calibration</button>
  </div>
</section>
<section>
  <div class="card">
    <h2>Status</h2>
    <div id="status">Idle</div>
    <pre id="log"></pre>
  </div>
  <div class="card" id="meas-card" style="display:none">
    <h2>Last measurement</h2>
    <div id="meas"></div>
  </div>
  <div class="card" id="cal-card" style="display:none">
    <h2>Calibration result</h2>
    <div id="cal"></div>
  </div>
</section>
</main>
<script>
const $ = (id) => document.getElementById(id);
const fields = ["smu_ip","port","current","limit","nplc","settle",
                "expected_rs","tolerance","runs","currents"];

function params() {
  const p = {};
  for (const f of fields) p[f] = $(f).value.trim();
  return p;
}

async function startTask(name) {
  if (name !== "board-test" && !$("smu_ip").value.trim()) {
    alert("Enter the SMU IP address first."); return;
  }
  if (name === "calibrate" && !$("expected_rs").value.trim()) {
    alert("Enter the calibration sample's known sheet resistance."); return;
  }
  const res = await fetch("/api/" + name, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(params()),
  });
  if (!res.ok) alert(await res.text());
}

function fmt(x, digits = 4) {
  return (x === null || x === undefined) ? "—" : Number(x).toExponential(digits);
}

function renderMeasurement(m) {
  if (!m) return;
  $("meas-card").style.display = "";
  let html = `<div class="big">${Number(m.sheet_resistance).toFixed(4)}
    <span class="unit">ohm/sq</span></div><table>`;
  for (const k of ["1","2","3","4"])
    html += `<tr><td>CFG ${k}</td><td>${fmt(m.voltages[k])} V</td></tr>`;
  html += `<tr><td>R horizontal</td><td>${Number(m.r_horizontal).toFixed(4)} ohm</td></tr>`;
  html += `<tr><td>R vertical</td><td>${Number(m.r_vertical).toFixed(4)} ohm</td></tr>`;
  html += `<tr><td>Current (readback)</td><td>${fmt(m.actual_current)} A</td></tr>`;
  if (m.resistivity !== null)
    html += `<tr><td>Resistivity</td><td>${fmt(m.resistivity)} ohm-cm</td></tr>`;
  $("meas").innerHTML = html + "</table>";
}

function renderCalibration(c) {
  if (!c) return;
  $("cal-card").style.display = "";
  const overall = c.passed
    ? '<span class="badge pass">SYSTEM CALIBRATED — PASS</span>'
    : '<span class="badge fail">CALIBRATION FAILED</span>';
  let html = `<p>${overall}</p><table>
    <tr><th>Check</th><th>Result</th><th>Detail</th></tr>`;
  for (const ch of c.checks) {
    const b = ch.passed ? '<span class="badge pass">PASS</span>'
                        : '<span class="badge fail">FAIL</span>';
    html += `<tr><td>${ch.name}</td><td>${b}</td><td>${ch.detail}</td></tr>`;
  }
  html += "</table>";
  if (c.mean_rs !== null)
    html += `<p>Mean Rs: <b>${Number(c.mean_rs).toFixed(4)}</b> ohm/sq
      (expected ${Number(c.expected_rs).toFixed(4)})</p>`;
  $("cal").innerHTML = html;
}

async function poll() {
  try {
    const s = await (await fetch("/api/status")).json();
    $("status").innerHTML = s.busy
      ? `<span class="busy">Running: ${s.task}…</span>` : "Idle";
    const log = $("log");
    log.textContent = s.log.join("\\n");
    log.scrollTop = log.scrollHeight;
    for (const b of ["btn-board","btn-measure","btn-cal"])
      $(b).disabled = s.busy;
    renderMeasurement(s.measurement);
    renderCalibration(s.calibration);
  } catch (e) { $("status").textContent = "Server unreachable"; }
  setTimeout(poll, 700);
}
poll();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    """Routes: GET / and /api/status, POST /api/<task>."""

    def log_message(self, *args: object) -> None:  # silence per-request noise
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif self.path == "/api/status":
            body = json.dumps(STATE.snapshot()).encode()
            self._send(200, body, "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        name = self.path.removeprefix("/api/")
        if name not in TASKS:
            self._send(404, b"unknown task", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            params = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, b"invalid JSON", "text/plain")
            return
        if not STATE.start_task(name):
            self._send(409, b"another operation is running", "text/plain")
            return
        _run_in_thread(name, params)
        self._send(200, b'{"started": true}', "application/json")


def serve(host: str = "127.0.0.1", port: int = 8432) -> None:
    """Start the GUI web server (blocks until Ctrl-C)."""
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"OpenPauw GUI running at http://{host}:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGUI stopped.")
