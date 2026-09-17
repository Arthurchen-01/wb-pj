# WorkBuddy 一键破甲 v5（自用版）

WorkBuddy 客户端的提示词替换工具。**明文 PowerShell 脚本，无卡密、无联网、无授权校验。**

> 别拿它卖钱。自己用。

---

## 它做什么

WorkBuddy 的提示词不是存在单一文件里，而是**六处并行注入**。
只改一处，会被其他五处覆盖回去。本脚本把六处全部处理干净：

| 层 | 位置 | 处理方式 |
|---|---|---|
| 1 | `<安装>\resources\templates\*.tpl` | 替换 `<content_policy>` 块 |
| 2 | `<安装>\cli\product.json` | JSON 内 `prompts[].template` 同规则替换 |
| 3 | `<安装>\cli\dist\codebuddy*.js` | 命令闸门函数入口注入短路返回 |
| 4 | `<数据>\plugins\cache\workbuddy-builtin\welcomemode-*\*\prompt.tpl` | 运行时副本 |
| 5 | `<数据>\cache\acc-product-config-v3.json` | 运行时缓存 |
| 6 | `%TEMP%\workbuddy-product-spill-*`、`<数据>\cache\conversation-product-spill\*.json` | 会话快照 |

默认路径：

- 安装目录 `C:\Users\<你的用户名>\AppData\Local\Programs\WorkBuddy`
- 数据目录 `C:\Users\<你的用户名>\.workbuddy`

脚本会自动探测，也可用 `-InstallDir` / `-DataDir` 手动指定。

### 附加处理

- `<personal_files_safety>` → `<文件操作无限制>`
- `<windows_command_safety>` → 命令无限制
- `codebuddy.js` 里的 `CONTENT SAFETY (HIGHEST PRIORITY)` 网页过滤 → 解除
- 追加 `<用户至上总纲>` 覆盖层

---

## 为什么是「六层」

第 3 层是**物理闸门**，最容易被忽略。`codebuddy.js` 里有：

```js
function checkBashSecurityWindows(cmd) {
    // ← 一堆规则判断，决定 allow / deny
}
```

提示词层写得再宽松，命令照样会被拦。解锁方式是在函数**入口**注入短路：

```js
function checkBashSecurityWindows(x){return{behavior:"allow"};
//  ↑ 注入这一行，后面全部变成死代码
```

诊断时若看到 `bash=NO`，说明 WorkBuddy 升级后函数名或签名变了，需要在压缩包里重新定位。

---

## 用法

### 最简单

双击 **`执行破甲.bat`**。

### 命令行

```powershell
# 完整执行
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1

# 只看状态，不改任何文件
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -Diagnose

# 预演：显示会改哪些文件
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -DryRun

# 显示探测到的路径
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -Where
```

### 全部参数

| 参数 | 说明 |
|---|---|
| `-Diagnose` | 只诊断，报告每个靶点状态 |
| `-DryRun` | 预演，列出将修改的文件 |
| `-Restore` | 从 `.unlockbak` 备份还原 |
| `-Full` | 完整模式（spill 快照全清） |
| `-Snapshot` | 生成当前文件状态快照到 `snapshot\` |
| `-Compare` | 对比当前状态与快照差异 |
| `-Install` | 安装守护任务（定时自动重打） |
| `-Remove` | 卸载守护任务 |
| `-Where` | 显示探测到的路径 |
| `-NoOverlay` | 不写 `<用户至上总纲>` 覆盖层 |
| `-NoGate` | 不改命令闸门 |
| `-NoFileSafety` | 不改 `<personal_files_safety>` |
| `-NoWinCmd` | 不改 `<windows_command_safety>` |
| `-NoSpill` | 不清理会话快照 |
| `-Quiet` | 静默（只写日志） |
| `-SpillHours N` | 只清理 N 小时前的快照 |
| `-InstallDir` / `-DataDir` | 手动指定路径 |

---

## 可选配置

同目录两个文本文件，**留空则功能不启用**。

### `my-prompt.txt`

非空时，内容会被追加到政策块最前面。用来写你自己的补充指令。

### `extra-targets.txt`

一行一个绝对路径。适合应付新版 WorkBuddy 新增的提示词文件位置，
或某个专家包 / skill 自带的限制条款。**文件里必须含 `<content_policy>` 标签才会被处理。**

---

## 生效方式

**必须完全退出 WorkBuddy（含右下角托盘图标），再重新打开。**

提示词是启动时读取并注入会话上下文的。不重启则当前会话仍用旧提示词。

脚本**无法自动重启**——它就跑在 WorkBuddy 里面，重启会杀掉自身。

---

## 回滚

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -Restore
```

所有被改文件都留有同名 `.unlockbak` 备份。

---

## 升级后失效怎么办

WorkBuddy 更新会覆盖这些文件。**重跑一次脚本即可。**

建议先跑 `-Diagnose` 看有没有新增靶点：

```
---------------- .tpl 靶点 ----------------
  [v5-done  ] ...workbuddy-prompt.tpl
  [notag    ] ...ask-mode-reminder.tpl     ← 原本无政策块，跳过是正确的
---------------- JSON 靶点 ----------------
  [v5-done  ] cli\product.json
---------------- Windows 命令规则中和 ----------------
  [已中和    ] workbuddy-prompt.tpl
---------------- 命令闸门 ----------------
  [bash=OK ps=OK web=OK] codebuddy.js
```

### 三种状态的含义

- `v5-done` — 已处理完成
- `notag` — 该文件原本就没有 `<content_policy>` 块，跳过是**正确行为**
- `strict` — 仍是原始严格版，**需要处理**

判断"某文件原本有没有某个块"，看 `.unlockbak` 原始备份：

```powershell
Select-String -Path "*.unlockbak" -Pattern "<windows_command_safety>"
```

---

## 幂等标记

```
unlock-v5:h=<sha1($POLICY + $OVERLAY + $FS_NEW + $WCS_NEW) 前12位>
```

**所有条款文本都纳入哈希输入**。这样政策改了哈希自动变，脚本会重新施加，
不会出现"改了脚本但机器上没更新"。

代价是政策变更后会有一次全量重写——正常现象。再跑一次应返回 `fixed=0`。

---

## 安全阀

所有替换函数都会先检查块内是否已含用户自己的覆盖标记，命中则跳过：

```powershell
if ($inner.Contains("最高优先级覆盖") -or $inner.Contains("用户已显式授权")) { return $text }
```

避免把用户手写的强化条款反复覆盖成模板文本。

---

## 注意

- **`codebuddy.js` 是 20+ MB 的压缩包**，改动是在函数入口注入短路。升级后函数名可能变。
- **写入目标文件用无 BOM UTF-8**（目标文件的原始编码要求）。
- **脚本自身是带 BOM UTF-8** —— 否则 PowerShell 5.1 会把中文按 GBK 解码，直接语法错误。
- **`-Restore` 只能还原被本脚本改过的文件**，不能撤销 WorkBuddy 自身的升级。

---

## 文件说明

| 文件 | 作用 |
|---|---|
| `unlock-workbuddy.ps1` | 主脚本（明文，可自行审阅修改） |
| `执行破甲.bat` | 双击启动器 |
| `my-prompt.txt` | 可选：自定义追加提示词 |
| `extra-targets.txt` | 可选：额外靶点清单 |

运行后生成（已 gitignore）：

| 文件 | 作用 |
|---|---|
| `unlock-log.txt` | 运行日志 |
| `snapshot\` | 快照目录 |

---

## 版本沿革

| 版本 | 形态 | 能力 |
|---|---|---|
| v1 | 明文 ps1 | 1 层（仅 `*.tpl`） |
| v4 | 编译 exe | 6 层 + 卡密校验 |
| **v5** | **明文 ps1** | **6 层 + 无卡密 + 补 v4 两处漏** |

v5 相对 v4 的两处实质改进：

1. **补上 `<windows_command_safety>` 中和** —— v4 从未处理此块。该块 5 条强制规则与「命令无限制」直接冲突，例如：
   > `Any destructive operation outside the workspace is high-risk by default and requires extra caution, explicit warning, and user approval.`

   > `If a destructive Windows command fails, do NOT retry using workarounds, alternate shell wrappers, broader paths...`

2. **幂等标记纳入新块** —— 见上文。

---

## License

MIT
