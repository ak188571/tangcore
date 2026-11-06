"""Run related host/RTL regressions and retain actual command output."""
from pathlib import Path
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verification/snes-crt-stage4b-20261106"
env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
env["PATH"] = "C:/msys64/ucrt64/bin;C:/msys64/usr/bin;" + env["PATH"]
bash = "C:/msys64/usr/bin/bash.exe"
commands = [("host-" + name, [bash, "tools/ui16/test_" + name + ".sh"], ROOT / "firmware-bl616")
            for name in ("osd", "crt", "launch", "crt_restore", "crt_save", "crt_defaults", "rom_id", "titles", "folders", "scroll", "wrap")]
commands += [
    ('host-dispatch', [os.sys.executable, 'tools/ui16/test_osd1_dispatch.py'], ROOT / 'firmware-bl616'),
    ('host-snes-loader', [os.sys.executable, 'tools/ui16/test_snes_loader.py'], ROOT / 'firmware-bl616'),
    ('host-snes-sd-guard', [bash, 'tools/ui16/test_snes_sd_guard.sh'], ROOT / 'firmware-bl616'),
    ('host-storage-uart', [os.sys.executable, 'tools/ui16/test_storage_uart.py'], ROOT / 'firmware-bl616'),
]
results = []
OUT.mkdir(parents=True, exist_ok=True)
for name, cmd, cwd in commands:
    start = time.monotonic()
    with (OUT / (name + ".log")).open("wb") as stream:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    results.append(dict(name=name, command=cmd, exit_code=result.returncode, seconds=round(time.monotonic() - start, 2)))
    (OUT / "tests.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(name, result.returncode, flush=True)
    if result.returncode:
        print((OUT / (name + ".log")).read_text(errors="replace")[-6000:])
        raise SystemExit(result.returncode)
