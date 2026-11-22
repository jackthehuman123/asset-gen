import subprocess
from pathlib import Path

from rbxasset.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def run_blender_script(script: str, *args: str) -> subprocess.CompletedProcess:
    blender = load_config(ROOT).blender
    result = subprocess.run(
        [
            blender, "-b", "--factory-startup", "--python-exit-code", "1",
            "--python", str(ROOT / "tests" / "blender_scripts" / script), "--", *args,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout + result.stderr).splitlines()[-60:])
        print(tail)
    assert result.returncode == 0, f"blender script {script} failed (rc={result.returncode})"
    return result
