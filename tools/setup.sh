#!/usr/bin/env bash
# Fresh machine: fonts, python venv with Playwright (for PDFs/screenshots), systemd service.
set -e
cd "$(dirname "$0")/.."
mkdir -p assets/fonts
[ -f assets/fonts/inter-latin.woff2 ] || {
  url=$(curl -s -A "Mozilla/5.0 Chrome/130 Safari/537.36" "https://fonts.googleapis.com/css2?family=Inter:wght@300..700&display=swap" | awk '/\/\* latin \*\//{f=1} f&&/url\(/{print;exit}' | grep -o "https[^)]*")
  curl -s -o assets/fonts/inter-latin.woff2 "$url"
}
# morphicons (MIT) is fetched, not vendored in git
[ -f assets/vendor/element.js ] || {
  mkdir -p assets/vendor /tmp/mp && curl -s https://registry.npmjs.org/morphicons/-/morphicons-1.7.1.tgz | tar xz -C /tmp/mp
  cp /tmp/mp/package/dist/{element.js,dom.js,controller-CXZuwJ_M.js,normalize-CYnN3Npw.js,spring-CFHloqPP.js} assets/vendor/
  cp /tmp/mp/package/LICENSE assets/vendor/morphicons-LICENSE
}
python3 -m venv .venv && .venv/bin/pip -q install playwright && .venv/bin/playwright install chromium && .venv/bin/playwright install-deps chromium || true
echo "Service: sudo cp tools/deckforge.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now deckforge"
echo "PIN: printed on first run, or: python3 tools/setpin.py 123456"
