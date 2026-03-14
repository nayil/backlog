#!/usr/bin/env bash
set -e

# ── Color helpers ────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Step 1: Detect Python 3.9+ ───────────────────────────────────────
info "Checking Python version..."

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python 3.9+ is required but not found. Please install Python 3.9 or later."
fi
info "Found: $($PYTHON --version)"

# ── Step 2: Install dependencies ─────────────────────────────────────
info "Installing dependencies from requirements.txt..."
if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    error "requirements.txt not found in $SCRIPT_DIR"
fi
"$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt" || \
    error "Failed to install dependencies. Check pip output above."
info "Dependencies installed."

# ── Step 3: Create launcher script ───────────────────────────────────
LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER="$LAUNCHER_DIR/backlog"

# Skip launcher creation in CI environments or with --no-launcher flag
if [ "${CI:-}" = "true" ] || [[ " $* " == *" --no-launcher "* ]]; then
    warn "Skipping launcher creation (CI or --no-launcher flag detected)."
else
    warn "Creating launcher at $LAUNCHER ..."
    mkdir -p "$LAUNCHER_DIR"
    cat > "$LAUNCHER" <<LAUNCHER_SCRIPT
#!/usr/bin/env bash
exec "$PYTHON" -m backlog "\$@"
LAUNCHER_SCRIPT
    chmod +x "$LAUNCHER"
    info "Launcher created: $LAUNCHER"
fi

# ── Done ──────────────────────────────────────────────────────────────
echo ""
info "Backlog Manager v1.0.0 installed successfully!"
echo ""
echo "  Run with:  python -m backlog"
if [ "${CI:-}" != "true" ] && [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo "  Or simply: backlog"
elif [ "${CI:-}" != "true" ]; then
    warn "Add ~/.local/bin to PATH to use the 'backlog' command:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
echo ""
