"""Inline figures/session_draws.json into figures/interactive.src.html and write ../interactive.html."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
draws = (HERE / "session_draws.json").read_text().strip()
src = (HERE / "interactive.src.html").read_text()
assert src.count("__DRAWS__") == 1
(HERE.parent / "interactive.html").write_text(src.replace("__DRAWS__", draws))
print("wrote", HERE.parent / "interactive.html")
