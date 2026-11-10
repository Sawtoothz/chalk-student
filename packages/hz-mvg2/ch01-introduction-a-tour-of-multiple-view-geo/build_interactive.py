"""Embed the scene data (session_model.scene_data) into interactive.html between the DATA markers.
Run from the package: python3 build_interactive.py"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import session_model as sm  # noqa: E402

data = sm.scene_data()
data["pitch0"] = 15.0
html = (HERE / "interactive.html").read_text()
new = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda m: "/*DATA*/" + json.dumps(data, separators=(",", ":")) + "/*END*/", html, count=1, flags=re.S)
(HERE / "interactive.html").write_text(new)
print("embedded", len(json.dumps(data)), "bytes")
