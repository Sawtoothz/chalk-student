# Chalk — command surface. `just` lists recipes.

set shell := ["bash", "-euo", "pipefail", "-c"]

# Every recipe runs inside the project virtualenv made by `uv sync`, so a bare `python3`,
# `uvicorn` or `marimo` resolves to .venv/bin and not to the system interpreter. In Docker the virtualenv is
# /opt/venv (VIRTUAL_ENV is set in the image), so a host's .venv in the mounted folder is never used there.
export PATH := env_var_or_default("VIRTUAL_ENV", justfile_directory() + "/.venv") + "/bin:" + env_var("PATH")
host := env_var_or_default("CHALK_HOST", "127.0.0.1")

default:
    @just --list

# Resolve package dir from book id and chapter number
_pkg book ch:
    @python3 scripts/pages.py {{book}} {{ch}} --dir

# Build the deterministic parts of a teaching package: annotated PDF, figures, Reader page.
# The content (highlights.json, lecture.md, ...) is written by the /teach skill in Claude Code.
teach book ch:
    #!/usr/bin/env bash
    pkg=$(python3 scripts/pages.py {{book}} {{ch}} --dir)
    read lo hi off < <(python3 scripts/pages.py {{book}} {{ch}} --range)
    pdf=$(python3 scripts/pages.py {{book}} {{ch}} --pdf)
    mkdir -p "$pkg"
    python3 scripts/highlight_pdf.py "$pdf" "$pkg/highlights.json" "$pkg/annotated.pdf" --first $((lo+off)) --last $((hi+off))
    [ -f "$pkg/figures/make_figures.py" ] && (cd "$pkg" && python3 figures/make_figures.py)
    just view {{book}} {{ch}}

# Chapter packages: check_package.py (files, figures, tests, session). Papers: check_paper.py (files, every file:line backed by code_refs.json).
# Optional third argument checks a package at another path, e.g. the gold example:
#   just check thrun-pr 3 examples/thrun-pr/ch03-gaussian-filters
check book ch pkg="":
    #!/usr/bin/env bash
    pkg="{{pkg}}"
    [ -n "$pkg" ] || pkg=$(python3 scripts/pages.py {{book}} {{ch}} --dir)
    if python3 scripts/pages.py {{book}} {{ch}} --json | grep -q '"kind": "paper"'; then python3 scripts/check_paper.py "$pkg"; else python3 scripts/check_package.py "$pkg"; fi

# Reader page. Works after any stage: tabs for files that do not exist yet are hidden.
view book ch:
    #!/usr/bin/env bash
    pkg=$(python3 scripts/pages.py {{book}} {{ch}} --dir)
    [ -f "$pkg/annotated.pdf" ] && python3 scripts/render_pages.py "$pkg/annotated.pdf" "$pkg/.pages"
    python3 scripts/build_viewer.py "$pkg" "$pkg/.pages" "$pkg/reader.html"
    echo "open $pkg/reader.html"

session book ch:
    #!/usr/bin/env bash
    nb="$(python3 scripts/pages.py {{book}} {{ch}} --dir)/session.py"
    if [ "{{host}}" = "127.0.0.1" ]; then exec marimo edit "$nb"; fi
    echo "In Docker: open the http://localhost:2718/?access_token=… address printed below (replace 0.0.0.0 with localhost)."
    exec marimo edit --headless --host {{host}} --port 2718 "$nb"

# Run the oracle tests against exercise.py and record the pass/fail count in learner.yaml
# (the record is what unlocks `just reveal`). Exit code is pytest's.
test book ch:
    #!/usr/bin/env bash
    set -uo pipefail
    root="$PWD"
    cd "$(python3 scripts/pages.py {{book}} {{ch}} --dir)"
    out=$(mktemp)
    python3 -m pytest exercises/tests -q 2>&1 | tee "$out"
    rc=${PIPESTATUS[0]}
    summary=$(tail -n 1 "$out"); rm -f "$out"
    passed=$(grep -oE '[0-9]+ passed' <<<"$summary" | grep -oE '[0-9]+' || echo 0)
    failed=$(( $(grep -oE '[0-9]+ (failed|error|errors)' <<<"$summary" | grep -oE '[0-9]+' | paste -sd+ - || echo 0) + 0 ))
    if [ "$passed" -gt 0 ] || [ "$failed" -gt 0 ]; then
        python3 "$root/scripts/learner.py" record-test {{book}} {{ch}} "$passed" "$failed"
        echo "recorded: $passed passed, $failed failed"
    fi
    exit $rc

# Finite-difference Jacobian check, run from the package dir (the recipe does not cd; arguments are passed as given). Model mode (Thrun-style exercises.models.<Model>.g/.h):
#   just fd exercises.exercise:G_jac --arg u --wrap 2
# Function mode, any callable on vectors or manifolds (--in/--out: euclid|so3-left|so3-right|se3-left|se3-right|module:func,
# SE(3) tangent xi = [rho; phi]); see scripts/fd_check.py's docstring, e.g. in packages/xu-fastlio2/paper:
#   just fd exercises.solutions.T3_solution:point_to_plane --point exercises.models:random_state --in exercises.models:boxplus --dim 24 --extra "(rng.normal(size=3), unit(rng.normal(size=3)), rng.normal(size=3))"
[no-cd]
[positional-arguments]
fd +args:
    python3 "{{justfile_directory()}}/scripts/fd_check.py" "$@"

# Reveal a gated solution. Refuses until tests have run once or all clues of that tier were opened.
reveal book ch tier:
    python3 scripts/learner.py reveal {{book}} {{ch}} {{tier}}

# Show clue n of an exercise and record it, e.g. just clue thrun-pr 3 T3.2 1
clue book ch exercise n:
    python3 scripts/learner.py clue {{book}} {{ch}} {{exercise}} {{n}}

# Record a test run (called by `just test`; also fine to call by hand)
progress:
    python3 scripts/learner.py progress

# Probe a PDF for its printed-to-pdf page offset
probe book:
    python3 scripts/pages.py {{book}} --probe

# Add a PDF to the library: just ingest ~/Downloads/cvx.pdf boyd-cvx [book|paper]
ingest pdf id kind="book":
    python3 scripts/ingest.py "{{pdf}}" --id {{id}} --kind {{kind}}

# Slide decks (stage `slides`): render slides/*.yaml to a stamped study-copy .pdf, check them, rebuild the Reader
slides book ch:
    #!/usr/bin/env bash
    pkg=$(python3 scripts/pages.py {{book}} {{ch}} --dir)
    python3 scripts/make_slides.py "$pkg"
    python3 scripts/check_slides.py "$pkg" || status=$?
    just view {{book}} {{ch}} >/dev/null
    exit ${status:-0}

# Run one /teach stage headlessly (what the GUI does): just stage thrun-pr 4 map | next
stage book ch stage="next":
    python3 scripts/run_stage.py {{book}} {{ch}} --stage {{stage}}

# AI engines (Claude Code, Codex, Gemini CLI, custom): which are installed and which one runs the stages (set on the GUI's AI page)
engines:
    python3 scripts/engines.py

# Anchor code references for a paper: just refs https://github.com/org/repo examples/x/paper/code_refs.json sym1 sym2 …
refs url out +symbols:
    python3 scripts/code_refs.py {{url}} --grep {{symbols}} --json {{out}}

# Every source and unit with its stage status, as JSON
list:
    python3 scripts/pages.py --list

# GUI mode: Library / Run / Reader at http://localhost:8765 (bind to a Tailscale address with --host)
serve host=host port="8765":
    uvicorn app.main:app --host {{host}} --port {{port}}

setup:
    uv sync
    @echo "put PDFs in library/ and fill books.yaml; then: just probe <book>"
