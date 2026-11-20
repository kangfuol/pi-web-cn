"""Re-apply the AbortSignal.any polyfill to pi-web's dist/client/index.html.

pi-web's client bundle calls AbortSignal.any (Chrome/Edge >= 116) when a
session is selected, so Edge 109 (last Edge on Win7) throws
"AbortSignal.any is not a function" and the session cannot be selected.
This inserts a small classic <script> polyfill immediately before the
module script. No-op on modern browsers (feature-detected).
Idempotent: does nothing if the marker is already present.
Must be re-run after `npm i -g @jmfederico/pi-web` upgrades, which
overwrite dist/client/index.html.
Usage: python3 /root/pi-web-polyfill/apply.py
"""
import sys

HTML = "/usr/lib/node_modules/@jmfederico/pi-web/dist/client/index.html"
MARKER = "AbortSignal.any polyfill (pi-web-polyfill"
POLYFILL = """<script>
/* AbortSignal.any polyfill (pi-web-polyfill, 2026-11-13): Edge/Chrome < 116 lacks AbortSignal.any (Edge 109 on Win7 is the last Win7 build). pi-web calls it when selecting a session. No-op on modern browsers. Re-apply after `npm i -g @jmfederico/pi-web` upgrades: /root/pi-web-polyfill/apply.py */
(function () {
  if (typeof AbortSignal === "undefined" || typeof AbortSignal.any === "function") return;
  AbortSignal.any = function (signals) {
    var controller = new AbortController();
    var onAbort = function () { controller.abort(); };
    for (var i = 0; i < signals.length; i++) {
      var s = signals[i];
      if (s.aborted) { controller.abort(); break; }
      s.addEventListener("abort", onAbort, { once: true });
    }
    return controller.signal;
  };
})();
</script>
"""

def main() -> int:
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    if MARKER in html:
        print("polyfill already present, nothing to do")
        return 0
    anchor = '<script type="module"'
    idx = html.find(anchor)
    if idx == -1:
        print("ERROR: module script tag not found in index.html", file=sys.stderr)
        return 1
    html = html[:idx] + POLYFILL + html[idx:]
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("polyfill injected before module script")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
