"""Replay two scripted work sessions against real HTTP and jq checks."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from time import perf_counter


HERE = Path(__file__).resolve().parent
PAYLOADS = {"health": {"status": "ok"}, "queue": {"pending": 1}, "version": {"version": "v1"}}
BASELINE = [
    ("activate", "health"), ("draft", "health"),
    ("activate", "queue"), ("draft", "queue"),
    ("activate", "version"), ("draft", "version"),
    ("finish", "health"), ("verify", "health"),
]
TREATMENT = [
    (action, feature)
    for feature in ("health", "queue")
    for action in ("activate", "draft", "finish", "verify")
]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def run(features, schedule, wip_limit):
    states = dict.fromkeys(features, "pending")
    events = []
    peak_wip = 0
    started = perf_counter()
    with TemporaryDirectory() as directory:
        root = Path(directory)
        handler = partial(QuietHandler, directory=directory)
        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
            thread.start()
            try:
                env = {**os.environ, "BASE_URL": f"http://127.0.0.1:{server.server_port}"}
                for action, feature in schedule:
                    event = {"action": action, "feature": feature}
                    target = root / f"{feature}.json"
                    if action == "activate":
                        active = list(states.values()).count("active")
                        if states[feature] != "pending" or (wip_limit and active >= wip_limit):
                            raise RuntimeError(f"Activation rejected: {feature}")
                        states[feature] = "active"
                    elif states[feature] != "active":
                        raise RuntimeError(f"Feature is not active: {feature}")
                    elif action == "draft":
                        target.write_text("{}\n", encoding="utf-8")
                    elif action == "finish":
                        target.write_text(json.dumps(PAYLOADS[feature]) + "\n", encoding="utf-8")
                    elif action == "verify":
                        check = subprocess.run(
                            ["bash", "-c", features[feature]["verification"]],
                            env=env, capture_output=True, text=True, timeout=5,
                        )
                        event.update(exit_code=check.returncode, output=check.stdout.strip(),
                                     stderr=check.stderr.strip())
                        if check.returncode == 0:
                            states[feature] = "passing"
                    active = list(states.values()).count("active")
                    peak_wip = max(peak_wip, active)
                    events.append({**event, "state": states[feature], "active": active,
                                   "elapsed_ms": round((perf_counter() - started) * 1000, 2)})
                files = list(root.glob("*.json"))
                lines = sum(len(file.read_text().splitlines()) for file in files)
                activated = sum(event["action"] == "activate" for event in events)
                verified = list(states.values()).count("passing")
                return dict(activated=activated, verified=verified, vcr=verified / activated,
                            peak_wip=peak_wip, artifact_lines=lines, states=states, events=events,
                            elapsed_ms=round((perf_counter() - started) * 1000, 2))
            finally:
                server.shutdown()
                thread.join()


def main():
    features = {item["id"]: item for item in json.loads((HERE / "feature_list.json").read_text())}
    result = {"unconstrained": run(features, BASELINE, None),
              "wip_1": run(features, TREATMENT, 1)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
