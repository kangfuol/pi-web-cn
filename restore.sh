#!/usr/bin/env bash
# restore.sh — pi-web 个人定制一键恢复（汉化 + 气泡主题 + Win7 补丁 + FCCP 品牌）
#
# 用途：pi-web 升级（npm i -g @jmfederico/pi-web）会覆盖
# dist/client/index.html，导致主题注入和 Win7 补丁丢失；汉化插件
# 本身不受升级影响，但这里一并检查，缺了就重装。
# 升级后在 Pi VPS 上跑一次即可，全部恢复。
#
# 用法（在 Pi VPS 上，root）：
#   cd /root/pi-web-cn && bash restore.sh
# 仓库 clone 位置就是本脚本所在的目录；脚本按自己所在目录找到
# theme/apply.py、polyfill/apply.py 和汉化插件文件。
# 幂等，可重复跑；每步都输出结果，最后汇总。
#
# 注意：只恢复本仓库里的个人定制，不动 nginx、证书、pi-auth、
# Pi 本体、会话数据。

set -u
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

THEME_DIR=/root/pi-web-theme
POLYFILL_DIR=/root/pi-web-polyfill
PLUGIN_DIR=/root/pi-web-plugins/language-chinese
PLUGIN_LINK=/root/.pi-web/plugins/language-chinese
CONFIG=/root/.config/pi-web/config.json
INDEX_HTML=/usr/lib/node_modules/@jmfederico/pi-web/dist/client/index.html

FAIL=0
step() { echo "== $1 =="; }
ok()   { echo "[OK] $1"; }
fail() { echo "[FAIL] $1"; FAIL=1; }

# ---------- 1. 汉化插件 ----------
step "1/5 汉化插件 language-chinese"
PLUGIN_OK=1
if [ ! -L "$PLUGIN_LINK" ] || [ ! -d "$PLUGIN_LINK" ]; then
  PLUGIN_OK=0
elif [ ! -f "$PLUGIN_LINK/pi-web-plugin.js" ] || [ ! -f "$PLUGIN_LINK/catalogs.js" ]; then
  PLUGIN_OK=0
fi
if [ "$PLUGIN_OK" = 1 ]; then
  ok "汉化插件已安装：$PLUGIN_LINK -> $(readlink "$PLUGIN_LINK")"
else
  echo "汉化插件缺失或不完整，正在重装……"
  mkdir -p "$PLUGIN_DIR"
  mkdir -p "$(dirname "$PLUGIN_LINK")"
  if [ -d "$PLUGIN_LINK" ] && [ ! -L "$PLUGIN_LINK" ]; then rm -rf "$PLUGIN_LINK"; fi
  cp "$REPO_DIR/catalogs.js" "$REPO_DIR/package.json" "$REPO_DIR/pi-web-plugin.js" "$PLUGIN_DIR/" \
    && ln -sfn "$PLUGIN_DIR" "$PLUGIN_LINK" \
    && [ -f "$PLUGIN_LINK/pi-web-plugin.js" ] && [ -f "$PLUGIN_LINK/catalogs.js" ] \
    && ok "汉化插件已重装：$PLUGIN_LINK -> $PLUGIN_DIR" \
    || fail "汉化插件重装失败"
fi

# ---------- 2. 气泡主题 ----------
step "2/5 气泡主题（黄气泡 / 灰气泡 / 白底 / 侧栏灰 / FCCP）"
mkdir -p "$THEME_DIR"
cp "$REPO_DIR/theme/apply.py" "$THEME_DIR/apply.py"
if python3 "$THEME_DIR/apply.py"; then
  if python3 "$THEME_DIR/apply.py" --check; then
    ok "主题已注入 index.html"
  else
    fail "主题 apply.py 跑了，但 --check 说注入器不在"
  fi
else
  fail "主题 apply.py 执行失败"
fi

# ---------- 3. Win7 旧浏览器补丁 ----------
step "3/5 Win7 补丁（AbortSignal.any polyfill，Edge 109）"
mkdir -p "$POLYFILL_DIR"
cp "$REPO_DIR/polyfill/apply.py" "$POLYFILL_DIR/apply.py"
if python3 "$POLYFILL_DIR/apply.py"; then
  ok "Win7 补丁已处理"
else
  fail "补丁 apply.py 执行失败"
fi

# ---------- 4. config.json：品牌 FCCP + 汉化启用 ----------
step "4/5 配置 /root/.config/pi-web/config.json"
if python3 - "$CONFIG" <<'EOF'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    cfg = json.load(f)
cfg["installationName"] = "FCCP"
cfg.setdefault("defaultLocalization", {})["language"] = "zh-CN"
cfg.setdefault("plugins", {}).setdefault("language-chinese", {})["enabled"] = True
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("installationName=FCCP, language=zh-CN, language-chinese enabled")
EOF
then
  ok "配置已确认：installationName=FCCP，汉化启用"
else
  fail "config.json 更新失败"
fi

# ---------- 5. 重启 pi-web + sessiond 并验证 ----------
step "5/5 重启 pi-web 并验证"
if XDG_RUNTIME_DIR=/run/user/0 systemctl --user restart pi-web.service pi-web-sessiond.service; then
  sleep 5
  if XDG_RUNTIME_DIR=/run/user/0 systemctl --user is-active --quiet pi-web.service; then
    ok "pi-web.service active"
  else
    fail "pi-web.service 重启后不是 active"
  fi
  if XDG_RUNTIME_DIR=/run/user/0 systemctl --user is-active --quiet pi-web-sessiond.service; then
    ok "pi-web-sessiond.service active"
  else
    fail "pi-web-sessiond.service 重启后不是 active"
  fi
else
  fail "systemctl restart 失败"
fi
if grep -q 'id="pi-web-bubble-injector"' "$INDEX_HTML"; then
  ok "index.html 里主题注入器在"
else
  fail "index.html 里找不到主题注入器"
fi
if grep -q 'AbortSignal.any polyfill' "$INDEX_HTML"; then
  ok "index.html 里 Win7 补丁在"
else
  fail "index.html 里找不到 Win7 补丁"
fi
if grep -q '<title>FCCP</title>' "$INDEX_HTML"; then
  ok "标签页标题是 FCCP"
else
  fail "标签页标题不是 FCCP"
fi
if curl -fsS -o /dev/null "http://127.0.0.1:8504/"; then
  ok "http://127.0.0.1:8504/ 可达"
else
  fail "http://127.0.0.1:8504/ 不可达"
fi

# ---------- 汇总 ----------
echo
if [ "$FAIL" = 0 ]; then
  echo "全部完成：汉化、主题、补丁、FCCP、重启验证都通过。刷新浏览器即可。"
  exit 0
else
  echo "有步骤失败（见上方 [FAIL]），请按提示检查后再跑一次 ./restore.sh。"
  exit 1
fi
