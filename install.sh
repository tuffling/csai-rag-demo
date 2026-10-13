#!/bin/sh
# One-line setup for the CSAI club RAG demo (Mac / Linux). Paste this into Terminal:
#
#   curl -LsSf https://raw.githubusercontent.com/tuffling/csai-rag-demo/main/install.sh | sh
#
# It installs uv (which installs Python for you), downloads the demo into ~/csai-rag-demo,
# and starts it. Paste the same line again any time to start the demo again.
set -e

REPO_ZIP="https://github.com/tuffling/csai-rag-demo/archive/refs/heads/main.zip"
DEST="$HOME/csai-rag-demo"

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -f "$DEST/rag.py" ]; then
  echo "==> Found the demo in $DEST (keeping any changes you made)"
else
  echo "==> Downloading the demo into $DEST ..."
  TMP="$(mktemp -d)"
  curl -LsSf "$REPO_ZIP" -o "$TMP/demo.zip"
  unzip -q "$TMP/demo.zip" -d "$TMP"
  mv "$TMP/csai-rag-demo-main" "$DEST"
  rm -rf "$TMP"
fi

cd "$DEST"
echo "==> Starting the demo (the first run downloads ~150 MB, hang tight)..."
if [ -n "$CI" ]; then
  uv run rag.py --setup
else
  uv run rag.py < /dev/tty
fi
