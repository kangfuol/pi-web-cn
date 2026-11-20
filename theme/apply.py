"""Inject the bubble chat style INTO pi-web's shadow roots.

Why a script and not a <style> in <head>: pi-web renders the whole UI inside
`pi-web-app`'s shadow DOM (chat lives in `document > pi-web-app > chat-view`).
Document-level CSS cannot cross a shadow boundary, so the rules must be
appended inside each open shadow root. CSS custom properties do inherit
through the boundary, which is why only colours appeared to change before.

This is server-side, so every device/browser gets it with no extension.
Idempotent; re-running replaces the injected block.

Usage: python3 /root/pi-web-theme/apply.py [--check|--remove]
"""
import json
import re
import sys

HTML = "/usr/lib/node_modules/@jmfederico/pi-web/dist/client/index.html"
SCRIPT_ID = "pi-web-bubble-injector"

CSS = """
/* ---- whole page background: pure white like Muse chat ---- */
html, body {
  --pi-initial-bg: #ffffff !important;
  --pi-bg: #ffffff !important;
  background: #ffffff !important;
}
:host {
  --pi-initial-bg: #ffffff !important;
  --pi-bg: #ffffff !important;
  --pi-selection-bg: #e9eaeb !important;
  --pi-accent: #6b7280 !important;
  --pi-accent-border: #d1d5db !important;
  --pi-surface-hover: #efeff0 !important;
}
/* ---- theme tokens: neutralize the purple accent at the source ---- */
/* pi-web paints selected/hover rows (and the inner .action-main) with
   var(--pi-selection-bg) / var(--pi-accent) / var(--pi-surface-hover).
   Custom properties inherit through shadow DOM, so overriding them here
   reaches every nested component and every state (:hover/:active/:focus/
   selected) even after Lit re-renders -- this stops purple coming back
   on click, which per-element rules alone could not do. */
html, body {
  --pi-selection-bg: #e9eaeb !important;
  --pi-accent: #6b7280 !important;
  --pi-accent-border: #d1d5db !important;
  --pi-surface-hover: #efeff0 !important;
}
/* ---- your messages: accent bubble, right aligned ---- */
article.msg[data-speaker="user"] {
  --ui-transcript-bg: #f8e1b6 !important;
  background: #f8e1b6 !important;
  margin-left: auto !important;
  margin-right: 16px !important;
  width: fit-content !important;
  max-width: min(80%, 42rem) !important;
  padding: 10px 16px !important;
  border: 0 !important;
  border-radius: 16px 16px 6px 16px !important;
  font-size: 16px !important;
  line-height: 1.6 !important;
}
/* ---- assistant output: neutral bubble, left aligned ---- */
article.msg[data-speaker="assistant"] {
  --ui-transcript-bg: #e9eaeb !important;
  background: #e9eaeb !important;
  margin-left: 16px !important;
  margin-right: auto !important;
  width: fit-content !important;
  max-width: min(100%, 58rem) !important;
  padding: 12px 16px !important;
  border: 1px solid #e9eaeb !important;
  border-radius: 16px 16px 16px 6px !important;
  font-size: 16px !important;
  line-height: 1.6 !important;
}
/* breathing room between turns */
article.msg[data-speaker="user"], article.msg[data-speaker="assistant"] {
  margin-top: 8px !important;
  margin-bottom: 8px !important;
}
/* event collapse rows: smaller, fainter, do not break the rhythm */
article.msg.event-group {
  font-size: 12px !important;
  line-height: 1.4 !important;
  opacity: 0.6 !important;
  padding-top: 2px !important;
  padding-bottom: 2px !important;
  margin-top: 2px !important;
  margin-bottom: 2px !important;
}
/* tool / system blocks stay plain */
article.msg.event-group, article.msg.tool, article.msg.system,
article.msg.tool-execution-shell, article.msg.ask-user-record-shell {
  border-radius: 0 !important;
}

/* ---- left sidebar + top tabs: gray, no more purple ---- */
/* sidebar panel background (was light purple from theme surface) */
aside#navigation-panel, app-navigation-panel, .navigation-sections {
  background: #f6f6f7 !important;
}
/* selected project / session rows: same gray as assistant bubble */
.action-row.selected, .tree-row.selected {
  background: #e9eaeb !important;
  box-shadow: inset 3px 0 0 #e9eaeb !important;
}
/* hover rows */
.action-row:not(.selected):hover, .tree-row:not(.selected):hover {
  background: #efeff0 !important;
}
/* inner content element also paints its own background -- cover it too,
   in selected AND hover states, so it cannot flash purple on click */
.action-row.selected .action-main, .tree-row.selected .action-main {
  background: #e9eaeb !important;
  border-color: #e9eaeb !important;
}
.action-row:not(.selected):hover .action-main, .tree-row:not(.selected):hover .action-main {
  background: #efeff0 !important;
}
/* active-path tint (was accent 7%) -> neutral gray */
.tree-row.active-path:not(.selected) {
  background: #efeff0 !important;
}
.tree-row.active-leaf {
  box-shadow: inset 3px 0 #e9eaeb !important;
}
/* selected primary tab (e.g. 聊天): gray, no accent underline */
.ui-tabs--primary .ui-tab:is(.selected, [aria-pressed="true"], [aria-current="page"]),
.ui-tabs--primary .ui-tab:is(.selected, [aria-pressed="true"], [aria-current="page"]):hover:not(:disabled) {
  background: #e9eaeb !important;
  box-shadow: none !important;
}
.ui-tab:is(.selected, [aria-pressed="true"], [aria-current="page"]) {
  background: #e9eaeb !important;
  box-shadow: none !important;
}
/* section headings in the sidebar (项目 / 会话): same light gray as the panel */
section > h2.ui-toolbar, .list-body > .subheading {
  background: #f6f6f7 !important;
}
"""

SCRIPT = """<script id="%s">
/* pi-web-bubble-injector (pi-web-theme/apply.py, 2026-11-19):
   pi-web's UI lives in shadow DOM, so document-level CSS cannot reach it.
   Append the bubble rules into every open shadow root instead.
   Re-apply after pi-web upgrades: python3 /root/pi-web-theme/apply.py */
(function () {
  var CSS = %s;
  function inject(root) {
    try {
      if (!root || !root.querySelector) return;
      if (root.querySelector('style[data-pwb]')) return;
      var s = document.createElement('style');
      s.setAttribute('data-pwb', '1');
      s.textContent = CSS;
      /* document itself cannot take appendChild (it already has a
         documentElement); put the light-DOM copy in <head> so the
         html/body rules (page bg + theme vars) actually apply. */
      if (root === document) {
        (document.head || document.documentElement).appendChild(s);
      } else {
        root.appendChild(s);
      }
    } catch (e) {}
  }
  /* top-bar brand: PI-WEB -> FCCP (only the machine-switcher label) */
  function rebrand(root) {
    try {
      if (!root || !root.querySelectorAll) return;
      var els = root.querySelectorAll('.machine-switcher-label bdi');
      for (var i = 0; i < els.length; i++) {
        if (els[i].textContent === 'PI-WEB') els[i].textContent = 'FCCP';
      }
    } catch (e) {}
  }
  function scanRoot(root) {
    inject(root);
    rebrand(root);
    var els = root.querySelectorAll('*');
    for (var i = 0; i < els.length; i++) {
      var sr = els[i].shadowRoot;
      if (sr) scanRoot(sr);
    }
  }
  function scan() { scanRoot(document); }
  /* keep scanning: Lit re-renders and newly created shadow roots (e.g. after
     navigation) need re-injection, and document-level MutationObserver cannot
     see inside shadow roots, so the interval must not stop after 60s. */
  setInterval(scan, 1000);
  var pending = false;
  new MutationObserver(function () {
    if (pending) return;
    pending = true;
    setTimeout(function () { pending = false; scan(); }, 200);
  }).observe(document.documentElement, { childList: true, subtree: true });
  scan();
})();
</script>
""" % (SCRIPT_ID, json.dumps(CSS))


def main() -> int:
    check = "--check" in sys.argv
    remove = "--remove" in sys.argv
    html = open(HTML, encoding="utf-8").read()
    pat = re.compile(r'<script id="%s">.*?</script>\n?' % re.escape(SCRIPT_ID), re.S)
    present = bool(pat.search(html))

    if check:
        print("bubble injector %s" % ("present" if present else "NOT present"))
        return 0 if present else 1
    if remove:
        open(HTML, "w", encoding="utf-8").write(pat.sub("", html))
        print("removed")
        return 0
    if present:
        html = pat.sub(lambda _: SCRIPT, html, count=1)
    else:
        if "</head>" not in html:
            print("ERROR: </head> not found", file=sys.stderr)
            return 2
        html = html.replace("</head>", SCRIPT + "</head>", 1)
    # browser tab title is static in index.html (JS never sets document.title),
    # so swap it here; apply.py re-applies it on every run.
    html = html.replace("<title>PI WEB</title>", "<title>FCCP</title>")
    open(HTML, "w", encoding="utf-8").write(html)
    print("updated" if present else "injected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
