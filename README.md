# pi-web 简体中文语言包

当前版本：**2026.11.19**（版本号按日期定，对应 pi-web 1.202611.5）

PI WEB（Pi Coding Agent 的 Web 界面）的简体中文语言包插件。官方 pi-web 只自带西班牙语和瑞典语语言包，这个包补上简体中文。

English: a Simplified Chinese language pack plugin for PI WEB. The official pi-web only ships Spanish and Swedish packs; this adds Simplified Chinese.

## 翻译范围

- 71 个命名空间，1829 条界面字符串，全部译自 pi-web **1.202611.5** 的英文原串
- 占位符、复数 / 选择分支、标签等 ICU 格式与英文原串逐条校验一致
- 未翻译的内容（品牌名、命令名、路径等）按原文保留
- 本版新增 `core.listReorder`（列表拖拽排序提示，2 条）和 `core.settingsRestart`（重启服务提示，6 条），均译自 1.202611.5 的英文原串；其余命名空间与 1.202611.2 版一致，未删任何已有翻译（经核对，1.202611.5 仍在使用全部已有命名空间）

## 安装

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

## 更新

pi-web 升级后新增或改名的字符串会回退显示英文，不会报错。更新步骤：

1. 从新版 pi-web 提取英文原串，对照 `zh-catalogs.json` 补翻新增的 key（占位符必须与英文原串完全一致）。
2. 运行 `python3 scripts/generate.py` 重新生成 `catalogs.js` 和 `pi-web-plugin.js`。
3. 替换服务器上的插件目录，刷新浏览器。

## 文件说明

- `pi-web-plugin.js` — 插件入口，向 PI WEB 注册 71 个命名空间的中文目录
- `catalogs.js` — 全部中文翻译（由 `zh-catalogs.json` 生成）
- `zh-catalogs.json` — 翻译源数据，`{命名空间: {key: 中文}}`
- `scripts/generate.py` — 从 `zh-catalogs.json` 生成上面两个 JS 文件
- `scripts/namespaces.json` — 命名空间顺序与来源文件（与瑞典语包的顺序一致）
- `package.json` — 插件清单（id：`language-chinese`）

## License

MIT
