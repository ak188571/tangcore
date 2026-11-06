"""S3a SNESTangのConsole138K buildと根拠を記録する。実機には書き込まない。"""
from pathlib import Path
from collections import Counter
from html import unescape
import hashlib
import json
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "snestang"
OUT = ROOT / "verification/snes-crt-stage3a-20261106"
BASELINE = "a142a290bbea9952e7bfea563d773e2b663665cb"
GOWIN = Path("C:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe")


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args]).decode().strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", BASELINE, "HEAD"], check=True)
    assert git("branch", "--show-current") == "tangcore-integrated"
    names = sorted({str(p.relative_to(REPO)).replace("\\", "/") for p in (REPO / "src").rglob("*") if p.is_file()} | {p.name for pattern in ("*.sdc", "*.tcl") for p in REPO.glob(pattern)})
    before = {name: sha(REPO / name) for name in names}
    command = [str(GOWIN), "build_console138k_usb.tcl", "console138k", "ds2"]
    start = time.monotonic()
    with (OUT / "fpga-build.log").open("wb") as log:
        result = subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
    record = {
        "target": "Console138K SNESTang stage3a horizontal blur",
        "baseline_commit": BASELINE, "source_head": git("rev-parse", "HEAD"),
        "working_tree_diff_sha256": hashlib.sha256(git("diff", "--binary", "HEAD").encode()).hexdigest(), "branch": "tangcore-integrated",
        "command": command, "exit_code": result.returncode,
        "seconds": round(time.monotonic() - start, 2),
        "tracked_file_sha256": before,
        "tracked_files_unchanged": before == {name: sha(REPO / name) for name in names},
        "device_programming_performed": False, "hardware_test_status": "pending",
    }
    destination = OUT / "fpga-build.json"
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    assert record["tracked_files_unchanged"], "Build modified tracked files"
    assert result.returncode == 0, "FPGA build failed; see fpga-build.log"
    log = (OUT / "fpga-build.log").read_text(errors="replace")
    assert "Placement and routing completed" in log and "Bitstream generation completed" in log
    assert not re.search(r"^ERROR\s", log, re.M)
    stem = "snestang_console138k_ds2"
    pnr = REPO / "impl/pnr"
    report = (pnr / (stem + "_tr_content.html")).read_text(encoding="utf-8")
    rows = []
    for row in re.findall(r"<tr>(.*?)</tr>", report, re.S):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)(?=</t[dh]>|<t[dh]\b|$)", row, re.S)
        rows.append([re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", c))).strip() for c in cells])
    summary = {r[0]: r[1] for r in rows if len(r) == 2}
    timing = {key: int(summary[key]) for key in (
        "Numbers of Setup Violated Endpoints", "Numbers of Hold Violated Endpoints")}
    pulse_rows = [r for r in rows if len(r) == 7 and r[4] in ("High Pulse Width", "Low Pulse Width") and r[0].isdigit()]
    resources = {k: int(v.split("(")[0]) for k, v in ET.parse(
        REPO / f"impl/gwsynthesis/{stem}_syn_rsc.xml").getroot().attrib.items() if k.startswith("T_")}
    for name in (stem + "_tr_content.html", stem + ".rpt.txt", stem + ".timing_paths", "cmd.do"):
        shutil.copy2(pnr / name, OUT / name)
    shutil.copy2(REPO / "console138k_combined.sdc", OUT / "console138k_combined.sdc")
    artifact = pnr / (stem + ".bin")
    record.update(timing=timing, synthesis_resources=resources,
                  reported_minimum_pulse_width_rows=pulse_rows,
                  artifact_bytes=artifact.stat().st_size, artifact_sha256=sha(artifact),
                  warning_counts=dict(Counter(re.findall(r"WARN\s+\(([^)]+)\)", log))))
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "tracked_file_sha256"}, indent=2), flush=True)
    assert not any(timing.values()), timing
    assert not any(float(r[1]) < 0 for r in pulse_rows), pulse_rows


if __name__ == "__main__":
    main()
