# pi-web 个人定制包（简体中文汉化 + 气泡主题 + 旧浏览器补丁）

当前版本：**2026.11.19**（版本号按日期定，对应 pi-web 1.202611.5）

PI WEB（Pi Coding Agent 的 Web 界面）的个人定制合集，只为自己用：简体中文语言包、对话气泡主题、旧浏览器补丁、顶栏品牌改名，升级后一条命令全部恢复。

English: a personal pi-web customization bundle — Simplified Chinese language pack, bubble chat theme, legacy-browser polyfill, and brand rename. One script restores everything after a pi-web upgrade.

## 包含什么

- **汉化插件**（`catalogs.js`、`pi-web-plugin.js`、`zh-catalogs.json`、`package.json`）：71 个命名空间，1829 条界面字符串，全部译自 pi-web **1.202611.5** 的英文原串。官方 pi-web 只自带西班牙语和瑞典语语言包，这个包补上简体中文。
- **气泡主题**（`theme/apply.py`）：服务端注入脚本。用户气泡靠右淡黄 `#f8e1b6`、Pi 气泡靠左浅灰 `#e9eaeb`、聊天区白底 `#ffffff`；左侧栏浅灰 `#f6f6f7`、选中行 `#e9eaeb`、悬停 `#efeff0`；顶栏品牌 `PI-WEB` 改成 `FCCP`、标签页标题改成 `FCCP`。任何电脑打开都有效，不用装浏览器扩展。
- **旧浏览器补丁**（`polyfill/apply.py`）：`AbortSignal.any` polyfill。Edge 109（Win7 最后一个 Edge 版本）没有 `AbortSignal.any`，点会话会报错选不上，加了这个补丁才能用；现代浏览器上自动跳过，没影响。
- **一键恢复脚本**（`restore.sh`）：升级后恢复上面全部定制，见下。

## 升级后恢复（一键）

pi-web 升级（`npm i -g @jmfederico/pi-web`）会覆盖 `dist/client/index.html`，主题注入和 Win7 补丁随之丢失；汉化插件本身不受升级影响，但恢复脚本一并检查。升级后在 Pi VPS 上跑一次即可：

```sh
cd /root/pi-web-cn && bash restore.sh
```

恢复脚本依次做：① 检查汉化插件在不在（缺了就从本仓库重装）；② 重跑主题 `theme/apply.py`；③ 重跑补丁 `polyfill/apply.py`；④ 确保 `~/.config/pi-web/config.json` 里品牌是 `FCCP`、汉化启用；⑤ 重启 pi-web 和 sessiond 并验证（注入器在、补丁在、标题是 FCCP、8504 可达）。每步都输出 `[OK]` / `[FAIL]`，脚本幂等，可重复跑。

## 汉化插件安装（首次）

本包只是界面翻译，不含任何 API key 或账号信息；模型 key 在 PI WEB 里按自己的配置登录即可，换台机器拉下来就能用。

PI WEB 语言包是浏览器插件，放在本地插件目录即可，无需重新编译 pi-web：

```sh
mkdir -p ~/.pi-web/plugins
ln -s /path/to/pi-web-cn ~/.pi-web/plugins/language-chinese
```

然后启用（二选一）：

- 在 `~/.config/pi-web/config.json` 里加：
  ```json
  {
    "plugins": { "language-chinese": { "enabled": true } },
    "defaultLocalization": { "language": "zh-CN" }
  }
  ```
  改完重启 web 服务（`pi-web restart`，只重启 web 服务不影响正在跑的会话），刷新浏览器即可。
- 或在界面里开：设置 → PI WEB 插件 → 启用 `language-chinese`，再到设置 → 通用 → 语言与地区选 Chinese / 中文。

## 汉化更新

pi-web 升级后新增或改名的字符串会回退显示英文，不会报错。更新步骤：

1. 从新版 pi-web 提取英文原串，对照 `zh-catalogs.json` 补翻新增的 key（占位符必须与英文原串完全一致）。
2. 运行 `python3 scripts/generate.py` 重新生成 `catalogs.js` 和 `pi-web-plugin.js`。
3. 替换服务器上的插件目录，刷新浏览器。

翻译范围说明：占位符、复数 / 选择分支、标签等 ICU 格式与英文原串逐条校验一致；未翻译的内容（品牌名、命令名、路径等）按原文保留。本版新增 `core.listReorder`（列表拖拽排序提示，2 条）和 `core.settingsRestart`（重启服务提示，6 条），均译自 1.202611.5 的英文原串；其余命名空间与 1.202611.2 版一致，未删任何已有翻译（经核对，1.202611.5 仍在使用全部已有命名空间）。

## 文件说明

- `pi-web-plugin.js` — 汉化插件入口，向 PI WEB 注册 71 个命名空间的中文目录
- `catalogs.js` — 全部中文翻译（由 `zh-catalogs.json` 生成）
- `zh-catalogs.json` — 翻译源数据，`{命名空间: {key: 中文}}`
- `scripts/generate.py` — 从 `zh-catalogs.json` 生成上面两个 JS 文件
- `scripts/namespaces.json` — 命名空间顺序与来源文件（与瑞典语包的顺序一致）
- `package.json` — 插件清单（id：`language-chinese`）
- `theme/apply.py` — 气泡主题注入脚本（服务端注入 index.html，升级后需重跑，见 `restore.sh`）
- `polyfill/apply.py` — Win7 补丁注入脚本（同上）
- `restore.sh` — 升级后一键恢复脚本（汉化检查 + 主题 + 补丁 + FCCP 配置 + 重启验证）

## License

MIT
