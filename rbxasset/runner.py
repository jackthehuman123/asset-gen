"""Runs headless Blender on a job. bpy-free, Python 3.9 compatible."""
import json
import subprocess
from pathlib import Path
from typing import Dict

from rbxasset.config import Config

ENTRY = Path(__file__).resolve().parent / "blender" / "entry.py"


class BuildError(Exception):
    pass


def run_blender(cfg: Config, job: Dict, timeout: int = 3600) -> Dict:
    """Write job.json next to the manifest, run entry.py, return the manifest dict.

    The combined log is saved to <job.out_dir>/build.log. On failure raises BuildError
    carrying the last 60 log lines.
    """
    out_dir = Path(job["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    job_path = out_dir / "job.json"
    job_path.write_text(json.dumps(job, indent=2))
    log_path = out_dir / "build.log"
    cmd = [cfg.blender, "-b", "--factory-startup", "--python-exit-code", "1",
           "--python", str(ENTRY), "--", str(job_path)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True, timeout=timeout)
        text, rc = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as e:
        partial = e.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        text, rc = partial + "\nTIMEOUT after %ss" % timeout, -1
    except OSError as e:
        raise BuildError("cannot run blender %r: %s" % (cfg.blender, e))
    log_path.write_text(text)
    manifest = Path(job["manifest_path"])
    if rc != 0 or not manifest.is_file():
        tail = "\n".join(text.splitlines()[-60:])
        raise BuildError("blender failed (exit %s); log %s\n%s" % (rc, log_path, tail))
    return json.loads(manifest.read_text())
