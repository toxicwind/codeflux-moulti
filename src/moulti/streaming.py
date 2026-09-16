"""`moulti stream`: ingest JSONL patch events from stdin into Moulti steps.

codeflux fork improvement — turns Moulti into a streaming sink for live
code-update pipelines. Each input line is one JSON event::

    {"type": "patch", "id": "evt-12", "title": "app.py modified",
     "file": "app.py", "diff": "<unified diff text>", "goal": "Rename foo"}
    {"type": "note", "text": "demo heartbeat 3/10"}

``patch`` events create one collapsible step per id (idempotent: re-sending an
id appends to the existing step) and pipe the diff text into it through the
regular ``moulti pass`` path. ``note`` events append to a shared stream-log
step. With ``--dry-run`` the moulti commands are printed, not executed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def _moulti(*args: str, input_bytes: bytes | None = None) -> int:
    proc = subprocess.run(["moulti", *args], input=input_bytes)
    return proc.returncode


def stream(args: dict[str, Any]) -> None:
    dry_run = bool(args.get("dry_run", False))
    seen: set[str] = set()
    log_step = "codeflux-stream-log"
    errors = 0
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"moulti stream: skipping bad JSON line: {exc}\n")
            errors += 1
            continue
        if not isinstance(ev, dict):
            sys.stderr.write("moulti stream: skipping non-object JSON line\n")
            errors += 1
            continue
        etype = ev.get("type", "patch")
        if etype == "note":
            step_id = log_step
            title = "codeflux stream log"
            text = str(ev.get("text", ""))
        else:  # patch event
            step_id = "codeflux-" + str(ev.get("id", "evt")).replace("/", "_")
            title = str(ev.get("title") or ev.get("file") or step_id)
            goal = ev.get("goal")
            text = (f"# goal: {goal}\n" if goal else "") + str(ev.get("diff", ""))
        if step_id not in seen:
            seen.add(step_id)
            cmd = ["step", "add", step_id, "--title", title]
            if dry_run:
                print("DRY: moulti", *cmd)
            else:
                rc = _moulti(*cmd)
                errors += rc != 0
        if dry_run:
            print(f"DRY: moulti pass {step_id} ({len(text)} bytes)")
        else:
            rc = _moulti("pass", step_id, input_bytes=text.encode())
            errors += rc != 0
    sys.exit(1 if errors else 0)
