#!/usr/bin/env python3
"""Regenerate pi-web-plugin.js and catalogs.js from zh-catalogs.json.

Usage: python3 scripts/generate.py

Reads:
  zh-catalogs.json        {namespace: {key: Simplified Chinese string}}
  scripts/namespaces.json ordered [{id, source}] list

Writes (repo root):
  catalogs.js             const catalogs = {...}; export default catalogs;
  pi-web-plugin.js        registers one catalog per namespace, locale zh-CN

Namespace order and source comments come from namespaces.json, which mirrors
the bundled Swedish pack's catalog order for pi-web 1.202611.2. When pi-web
adds or renames strings, update zh-catalogs.json first (translate the new keys,
keeping every ICU placeholder/tag exactly as in the English source), then run
this script.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def main() -> None:
    zh = json.loads((ROOT / "zh-catalogs.json").read_text(encoding="utf-8"))
    namespaces = json.loads(
        (ROOT / "scripts" / "namespaces.json").read_text(encoding="utf-8")
    )
    order = [n["id"] for n in namespaces]
    comments = {n["id"]: n["source"] for n in namespaces}
    assert set(order) == set(zh), set(order) ^ set(zh)

    lines = [
        "// Language pack for PI WEB, mirroring the bundled Swedish pack.",
        "// Full namespaces follow the host and bundled plugins' registerMessages calls.",
        "const catalogs = {",
    ]
    for ns in order:
        lines.append(f"    // {comments[ns]}")
        lines.append(f"    {js_str(ns)}: {{")
        for key, value in zh[ns].items():
            lines.append(f"        {js_str(key)}: {js_str(value)},")
        lines[-1] = lines[-1].rstrip(",")
        lines.append("    },")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("};")
    lines.append("export default catalogs;")
    (ROOT / "catalogs.js").write_text("\n".join(lines) + "\n", encoding="utf-8")

    plugin = """// Language pack for PI WEB, hand-built mirroring the bundled Swedish pack.
// Register metadata eagerly; translation text loads only when Chinese is requested.
const namespaces = [
""" + "".join(f"    {js_str(ns)},\n" for ns in order) + """];

const plugin = {
    apiVersion: 5,
    name: "Chinese / 中文",
    activate: ({ localization }) => {
        if (localization === undefined)
            throw new Error("Chinese requires a localization-capable PI WEB host");
        for (const namespace of namespaces) {
            localization.registerCatalog({
                id: namespace,
                namespace,
                locale: "zh-CN",
                load: async () => {
                    const { default: catalogs } = await import("./catalogs.js");
                    const catalog = catalogs[namespace];
                    if (catalog === undefined)
                        throw new Error(`Missing Chinese catalog: ${namespace}`);
                    return catalog;
                },
            });
        }
        return { contributions: {} };
    },
};
export default plugin;
"""
    (ROOT / "pi-web-plugin.js").write_text(plugin, encoding="utf-8")
    total = sum(len(v) for v in zh.values())
    print(f"wrote catalogs.js and pi-web-plugin.js: {len(order)} namespaces, {total} keys")


if __name__ == "__main__":
    main()
