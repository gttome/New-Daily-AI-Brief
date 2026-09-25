import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"site/command-center"
subprocess.run(["node","build.mjs"],cwd=root,check=True)
subprocess.run(["node","--test",*[str(p) for p in sorted((root/"test").glob("*.mjs"))]],cwd=root,check=True)
