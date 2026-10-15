import subprocess
import time
import os

exe = r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
uproj = r"D:\Projects\Substrate\Substrate.uproject"

print(f"Launching {exe} with {uproj}...")
proc = subprocess.Popen([exe, uproj, "-stdout", "-unattended"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
print(f"Started UnrealEditor with PID {proc.pid}")
