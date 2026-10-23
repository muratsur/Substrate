"""Package a Windows Shipping build and record build provenance.
Usage: python _tools/package_shipping.py <BuildName> [--skip-preflight]
Runs _tools/preflight_collision.py first (editor must be open) and refuses to package if it fails."""
import subprocess
import sys
import os
import time
import hashlib
import json
from pathlib import Path

if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
    sys.exit(__doc__)
NAME = sys.argv[1]
if '--skip-preflight' not in sys.argv and subprocess.call([sys.executable, str(Path(__file__).with_name('preflight_collision.py'))]) != 0:
    sys.exit('preflight_collision failed: fix the listed actors (or pass --skip-preflight) before packaging')

TIMESTAMP = time.strftime('%Y%m%d_%H%M%S')
UAT = r"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat"
UPROJ = r"D:\Projects\Substrate\Substrate.uproject"
CANDIDATE_ID = f"Windows_{NAME}_{TIMESTAMP}"
ARCHIVE_DIR = Path(rf"D:\Projects\Substrate\Packaged\{CANDIDATE_ID}")
LOG_FILE = Path(rf"D:\Projects\Substrate\Saved\Logs\package_build_{NAME.lower()}_{TIMESTAMP}.log")
EVIDENCE_DIR = Path(rf"D:\Projects\Substrate\_evidence\builds")
INI_FILE = Path(r"D:\Projects\Substrate\Config\DefaultEditorPerProjectUserSettings.ini")

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Temporarily disable bAutoStartServer in ini during cooking so cooker commandlet doesn't conflict on port 8000
ini_original = INI_FILE.read_text(encoding="utf-8") if INI_FILE.exists() else ""
ini_modified = ini_original.replace("bAutoStartServer=True", "bAutoStartServer=False")

cmd = [
    UAT,
    "BuildCookRun",
    f"-project={UPROJ}",
    "-noP4",
    "-platform=Win64",
    "-clientconfig=Shipping",
    "-build",
    "-cook",
    "-stage",
    "-pak",
    "-package",
    "-archive",
    f"-archivedirectory={ARCHIVE_DIR}",
    "-unattended",
    "-utf8output"
]

print("=================================================================")
print(f"=== BUILDING SHIPPING CANDIDATE: {CANDIDATE_ID} ===")
print("=================================================================")
start_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
start_ts = time.time()
print(f"Start Time:   {start_time_str}")
print(f"UAT Command:  {' '.join(cmd)}")
print(f"Archive Dir:  {ARCHIVE_DIR}")
print(f"Log File:     {LOG_FILE}")

warnings_list = []
errors_list = []

try:
    if ini_modified != ini_original:
        print("Temporarily setting bAutoStartServer=False in ini for cook...")
        INI_FILE.write_text(ini_modified, encoding="utf-8")

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- BUILD STARTED: {start_time_str} ---\n")
        f.write(f"Command: {' '.join(cmd)}\n\n")
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        last_print = time.time()
        for line in p.stdout:
            f.write(line)
            f.flush()
            line_clean = line.strip()
            
            if "warning:" in line_clean.lower() or "warning " in line_clean.lower():
                warnings_list.append(line_clean)
            if "error:" in line_clean.lower() or "error " in line_clean.lower() or "fatal" in line_clean.lower():
                errors_list.append(line_clean)
                
            now = time.time()
            if any(k in line_clean for k in [
                "Running AutomationTool", "BUILD SUCCESSFUL", "Cooking", "Cooked packages",
                "Copying NonUFSFiles", "Packaging", "ARCHIVE", "AutomationTool exiting",
                "BUILD FAILED", "Fatal Error", "Success"
            ]) or (now - last_print > 15):
                print(f"[{time.strftime('%H:%M:%S')}] {line_clean[:120]}", flush=True)
                last_print = now

        p.wait()

finally:
    if ini_original:
        print("Restoring original ini (bAutoStartServer=True)...")
        INI_FILE.write_text(ini_original, encoding="utf-8")

end_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
elapsed_sec = time.time() - start_ts
exit_code = p.returncode

print(f"\nUAT Process Exited with Code: {exit_code} in {elapsed_sec/60.0:.2f} minutes")
print(f"Total Warnings: {len(warnings_list)}")
print(f"Total Errors:   {len(errors_list)}")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

launcher_exe = ARCHIVE_DIR / "Substrate.exe"
game_exe_hybrid = ARCHIVE_DIR / "Substrate" / "Binaries" / "Win64" / "Substrate-Win64-Shipping.exe"
game_exe_content = ARCHIVE_DIR / "Engine" / "Binaries" / "Win64" / "UnrealGame-Win64-Shipping.exe"
game_exe = game_exe_hybrid if game_exe_hybrid.exists() else game_exe_content
paks_dir = ARCHIVE_DIR / "Substrate" / "Content" / "Paks"

provenance_data = {
    "candidate_id": CANDIDATE_ID,
    "timestamp": TIMESTAMP,
    "build_start": start_time_str,
    "build_end": end_time_str,
    "elapsed_seconds": round(elapsed_sec, 2),
    "exit_code": exit_code,
    "archive_dir": str(ARCHIVE_DIR),
    "log_file": str(LOG_FILE),
    "warning_count": len(warnings_list),
    "error_count": len(errors_list),
    "files": {}
}

if launcher_exe.exists():
    provenance_data["files"]["launcher_exe"] = {
        "path": str(launcher_exe),
        "size_bytes": launcher_exe.stat().st_size,
        "sha256": compute_sha256(launcher_exe)
    }

if game_exe.exists():
    provenance_data["files"]["game_exe"] = {
        "path": str(game_exe),
        "size_bytes": game_exe.stat().st_size,
        "sha256": compute_sha256(game_exe)
    }

if paks_dir.exists():
    for f in paks_dir.glob("*.pak"):
        provenance_data["files"][f.name] = {
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "sha256": compute_sha256(f)
        }
    for f in paks_dir.glob("*.ucas"):
        provenance_data["files"][f.name] = {
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "sha256": compute_sha256(f)
        }

prov_file = EVIDENCE_DIR / f"build_provenance_{TIMESTAMP}.json"
with open(prov_file, "w", encoding="utf-8") as f:
    json.dump(provenance_data, f, indent=2)

print(f"\nBuild Provenance saved to: {prov_file}")
sys.exit(exit_code)
