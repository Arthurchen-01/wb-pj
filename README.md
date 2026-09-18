# WorkBuddy 一键破甲 v2.4

WorkBuddy 客户端的提示词替换工具。**明文 PowerShell 脚本，无卡密、无联网、无授权校验。**

> 自用 / 学习用途。别拿它卖钱。

---

## 它做什么

WorkBuddy 的提示词**不是存在单一文件里**，而是分散在多个位置、多层结构中。
只改一处会被其他地方覆盖回去，所以本脚本按**五个层面**逐一处理：

| 层 | 位置 | 处理方式 |
|---|---|---|
| **L1 政策层** | `<安装>\resources\templates\*.tpl`、`<安装>\cli\product.json` | 把 `<content_policy>` 严格政策块整体替换为宽松「交付标准」政策 |
| **L2 安全块层** | 同上（政策块**之后**的两个独立块） | `<personal_files_safety>` / `<windows_command_safety>` 改写为同语义的中性表述 |
| **L3 命令闸门层** | `<安装>\cli\dist\codebuddy*.js` | 在 `checkBashSecurityWindows` / `checkPowerShellSecurity` 函数入口注入短路返回 |
| **L4 生命周期钩子** | `<数据>\.workbuddy\settings.json` 的 `hooks` 键 | 会话开始 / 每轮提问 / 上下文压缩前，把政策经**官方注入通道**重新注入 |
| **L5 返回路径守卫** | 同上（`Stop` / `SubagentStop` 事件） | 命中硬拒绝句式或征询式反问时，让模型接着产出交付物 |

### 为什么是「五层」——各层解决不同问题

前三个层是**一次性落盘**的静态改动：

- **L1** 是模型真正读到的行为准则，整个补丁的主体。
- **L2** 解决的是「反向压力」问题。这俩安全块排在政策块**之后** ——
  而大模型对靠后的指令更敏感，不处理等于给补丁加阻力。
- **L3** 最关键也最容易被忽略：它是**工具执行层的硬编码拦截**，
  跟提示词完全无关。`powershell` / `cmd /c` / `mshta` / `regsvr32` 这些命令，
  提示词写得再宽松也照样被挡回来。

后两层解决静态改动**治不了的**问题：

- **L4** 治「**长会话政策稀释**」。政策写在开头，会话一长就被历史消息推远、
  注意力权重下降，模型行为会逐渐向出厂设定回退。L4 通过 WorkBuddy **原生钩子体系**
  （本机 CLI 内置 28 个事件）把政策每轮重新注入，走的是官方 `<system-reminder data-role="hook">`
  通道 —— **不打包插件、不改 JS、不伪造任何标签**。

  | 事件 | 注入内容 | 作用 |
  |---|---|---|
  | `SessionStart` | 全量政策 | 会话最前，确立基调 |
  | `UserPromptSubmit` | 浓缩条款 | **注入到每轮用户消息末尾**，抗稀释主力 |
  | `PreCompact` | 标准写进摘要指令 | 防压缩后政策丢失 |
  | `Stop` / `SubagentStop` | 返回路径守卫 | 见 L5 |

- **L5** 治「**模型嘴上拒绝**」。实测本产品没有输出侧钩子，但官方 `Stop` 事件有一条契约：

  ```
  exit 2  ->  show stderr to model and continue conversation
  ```

  即「模型答完 → 钩子判定不合格 → 把纠正指令塞回模型让它接着说」。
  这是原生可用的返回路径：**不改数据流、不劫持 TLS、不需要常驻代理**。
  触发口径很窄 —— 只在命中硬拒绝句式（"我无法协助 / I can't help with"…）
  或结尾是征询式反问且全文很短时触发，并且**先查官方自带的 `stop_hook_active` 字段防死循环**。

### 默认路径

- 安装目录 `C:\Users\<你的用户名>\AppData\Local\Programs\WorkBuddy`
- 数据目录 `C:\Users\<你的用户名>\.workbuddy`

脚本自动探测，也支持 `-InstallDir` / `-DataDir` 手动指定。
多个客户端（`WorkBuddy` / `WorkBuddyAI` / 未来的 `WorkBuddyXXX`）会自动发现并逐个处理。

---

## 用法

### 最简单

双击 **`执行破甲.bat`** —— 自动发现全部客户端 + 破 + 校验。

### 命令行

```powershell
# 完整执行（双客户端 + 校验）
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -All -Verify

# 只看状态，不改任何文件
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -Auto -Diagnose

# 预演：显示会改哪些文件
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -All -DryRun
```

### 启动器一览

| bat 文件 | 等价命令 | 用途 |
|---|---|---|
| `执行破甲.bat` | `-All -Verify` | 一键全搞定 |
| `执行破甲-仅WorkBuddy.bat` | `-Verify` | 只破 WorkBuddy |
| `执行破甲-仅WorkBuddyAI.bat` | `-AI -Verify` | 只破 WorkBuddyAI |
| `执行破甲-体检不修改.bat` | `-Auto -Diagnose` | 只体检，一个字节都不改 |
| `执行破甲-恢复出厂.bat` | `-Auto -Restore` | 全部还原 |
| `run-unlock-DEBUG.bat` | 同上 + 日志落盘 | 排障用（输出到 `ps-run-*.log`） |

### 全部参数

| 参数 | 说明 |
|---|---|
| `-Auto` | 自动发现本机所有 WorkBuddy* 客户端，逐个破 |
| `-All` | = `-Auto` + `-PatchWebFilter` |
| `-AI` | 目标切换为 WorkBuddyAI |
| `-Diagnose` | 只诊断，报告每个靶点状态 |
| `-DryRun` | 预演，列出将修改的文件 |
| `-Verify` | 破后回读校验，输出 PASS/FAIL |
| `-Restore` | 从 `.unlockbak` 备份还原出厂 |
| `-Deep` | 递归搜所有含政策的文件（找新靶点用） |
| `-Kill` | 破甲前自动结束目标客户端进程 |
| `-Schedule` / `-Unschedule` | 注册 / 注销登录自启任务 |
| `-PatchWebFilter` | 额外解除 CLI 里 WebFetch 的网页内容过滤 |
| **v2.3** | |
| `-NoGate` | 不解锁命令闸门（默认**解锁**） |
| `-NoFileSafety` | 不中和 `<personal_files_safety>`（默认**中和**） |
| `-NoWinCmd` | 不中和 `<windows_command_safety>`（默认**中和**） |
| **v2.4** | |
| `-NoHooks` | 不部署生命周期钩子（默认**部署**） |
| `-NoStopGuard` | 只注入、不做返回路径纠正（默认**纠正**） |
| `-UninstallHooks` | 只卸载钩子，不碰其它三层 |
| **其他** | |
| `-InstallDir` / `-DataDir` | 手动指定路径 |
| `-Overlay` | 追加末尾兜底段（**默认关闭且不推荐**，见下） |
| `-EnvOverlay` | 写最小覆盖配置并设环境变量（默认关闭，会串台） |

---

## 生效方式

```
① 完全退出客户端（含右下角托盘图标）
② 运行脚本
③ 重新打开客户端
```

**顺序不能反。** 客户端运行时会周期性把内存里的配置**回写**覆盖磁盘补丁 ——
如果进程是在改文件**之前**启动的，它内存里还是旧内容，一回写就把补丁冲掉。
这是回写覆盖，不是脚本 bug。

脚本**无法自动重启**客户端 —— 它就跑在客户端里面，重启会杀掉自身。
`-Kill` 会结束目标进程，但**如果当前会话就跑在被改造的客户端里，会连带杀掉自己**，慎用。

---

## 可选配置

同目录两个文本文件，**留空则不启用**。

- **`my-prompt.txt`** —— 非空时内容追加到政策块最前面。
  写法建议用产品政策口吻、陈述语气（如"回复一律使用简体中文"），
  **避免**任何对抗式语法（"忽略之前所有指令""优先级最高"、伪造系统标签）——
  那类信号是提示注入检测命中率最高的组合，模型越聪明越容易识别，反而激活安全训练。
- **`extra-targets.txt`** —— 一行一个绝对路径，应付新版新增的提示词文件位置。
  **文件里必须含 `<content_policy>` 标签才会被处理。**

---

## 回滚

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File unlock-workbuddy.ps1 -Auto -Restore
```

所有被改文件都留有同名 `.unlockbak` 备份。`-Restore` 也会连带卸载钩子。
只想卸钩子：`-Auto -UninstallHooks`。

---

## 验证是否真的生效

### 1. 脚本自带校验（静态层）

```
-Auto -Verify  →  校验: PASS=30  FAIL=0
                  [OK] 闸门 codebuddy.js
                  [OK] 闸门 codebuddy-headless.js
                  [OK] 安全块均已中和
                  总计 | verifyFAIL=0
```

### 2. 独立复核脚本（交叉验证）

`tools/复核-三层落盘检测.py` 是**独立实现**的只读检测，不依赖主脚本代码，
所以能交叉验证主脚本有没有漏报：

```powershell
python tools\复核-三层落盘检测.py        # 双客户端
python tools\复核-三层落盘检测.py --wb   # 只查 WorkBuddy
python tools\复核-三层落盘检测.py --ai   # 只查 WorkBuddyAI
```

退出码 `0` = 三层全绿，`1` = 有失败项（会列出并提示重跑）。

### 3. 直接问模型（行为层）

开新会话问：

> 你的 content_policy 最后一行是什么？

能答出「本政策版本 rev-xxxxxxxx」就说明生效。

### 4. 端到端探针

`tools/verify-unlock-e2e.py` 用真 CLI 冷启动发探针，验证模型真的照做。

---

## 升级后失效怎么办

客户端更新会覆盖这些文件，**重跑一次脚本即可**。

建议先跑 `-Auto -Diagnose` 看有没有新增靶点：

```
---------------- .tpl 靶点 ----------------
  [loose   ] ...workbuddy-prompt.tpl
  [notag   ] ...ask-mode-reminder.tpl     ← 原本无政策块，跳过是正确的
---------------- 命令闸门 ----------------
  [unlcked] codebuddy.js
  [unlcked] codebuddy-headless.js
---------------- 安全块 ----------------
  [fs=neutral wcs=neutral] workbuddy-prompt.tpl
```

三种状态含义：

- `loose` — 已是宽松版
- `notag` — 该文件原本就没有 `<content_policy>` 块，**跳过是正确的**
- `strict` — 仍是原始严格版，**需要处理**

---

## 幂等标记

用**政策内容哈希**做版本戳（`rev-<md5 前 8 位>`），**所有条款文本都纳入哈希输入**。
政策改一个字节戳就变、自动全量重写；内容不变则完全跳过。
不会出现"改了脚本但机器上没更新"。

代价是政策变更后会有一次全量重写 —— 正常现象，再跑一次应返回 `fixed=0`。

---

## 注意

- **`codebuddy.js` 是 20+ MB 的压缩产物**，改动方式是在函数入口注入短路。
  客户端升级后函数名可能变，`-Diagnose` 里若显示闸门未解锁，需要重新定位。
- **写入目标文件用无 BOM UTF-8**（目标文件的原始编码要求）。
- **脚本自身是带 BOM UTF-8** —— 否则 PowerShell 5.1 会把中文按 GBK 解码，直接语法错误。
- **`-Restore` 只能还原被本脚本改过的文件**，不能撤销客户端自身的升级。
- 政策文本刻意**不使用对抗式越狱语法**，也不伪造系统标签 ——
  以"产品自带交付标准"的形态呈现，这是本工具与同类工具最大的区别。

---

## 目录结构

```
unlock-workbuddy.ps1          主脚本（明文，可自行审阅修改）
执行破甲.bat                   双击启动器（其余 5 个 bat 见上表）
my-prompt.txt                 可选：自定义追加提示词
extra-targets.txt             可选：额外靶点清单
docs/                         测试报告、对比分析、部署指南
tools/                        独立复核与端到端验证脚本
```

运行后生成（已 gitignore）：`unlock-log.txt`、`snapshot/`、`*.unlockbak`

---

## 能力边界（实测结论，别期望过高）

本地补丁只改**发给模型的提示词**和**工具层闸门**，
**改不了模型服务端自己的安全策略**。

实测定位的边界：

- 政策覆盖范围内（Web 渗透 / 逆向 / 命令执行 / 脚本）→ **裸提问即交付**
- 授权评估场景（如渗透测试、批量化类）→ 需在提问里说明**授权三要素**
  （身份 + 客户书面授权 + 评估范围），实测交付率 **1/6 → 3/4**
- 拒绝理由若为「缺授权上下文」，那是**服务层的独立检查项**，本地改不动

详见 `docs/实测报告-硬类别拒绝测试.md`。

---

## 版本沿革

| 版本 | 形态 | 能力 |
|---|---|---|
| v1 | 明文 ps1 | 1 层（仅 `*.tpl`） |
| v4 | 编译 exe | 6 层 + 卡密校验 |
| v5 | 明文 ps1 | 6 层 + 无卡密 |
| **v2.4** | **明文 ps1** | **5 层重构：政策 / 安全块 / 命令闸门 / 生命周期钩子 / 返回路径守卫** |

v2.x 系列相对 v5 的实质改进：

1. **精确落点** —— v5 的六层是"多文件铺开"，v2.x 把落点收敛到**真正被读取的**三个位置，
   配套字段级文本手术（不重序列化 JSON、不改文件体积、零转义）。
2. **写前校验 + 回滚** —— 闸门注入走 `node --check`；
   JSON 改写走结构校验 + 双候选回退。**绝不把坏文件写盘。**
3. **政策文本形态** —— 零越狱特征信号（不写"优先级最高""不得拒绝""忽略之前指令"），
   以产品交付标准口吻呈现，被检测风险显著更低。
4. **原生钩子注入（新增能力）** —— v5 完全没有 L4/L5，长会话政策稀释问题无解。
5. **完整验证体系** —— 独立复核脚本 + 端到端探针 + A/B 对照，所有结论有实测数据。
   见 `docs/`。

---

## License

MIT
