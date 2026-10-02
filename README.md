# 🌞 学习专注倒计时（Study Focus Countdown）

> 一个让你快速进入心流状态的学习倒计时工具。
> A convenient study countdown device that helps you enter a state of flow.

**单文件 HTML，零依赖，双击即用，可完全离线运行。** 白天有太阳、云朵与彩虹，夜晚有月亮、星空与流星；每分钟换一句鼓励语，到点用合成铃声提醒你休息。

---

## ✨ 功能特性

| 功能 | 说明 |
| --- | --- |
| 🕐 自定义时长 | 输入 1–180 分钟，默认 25 分钟（番茄钟节奏） |
| ⏱️ 高精度计时 | 基于 `Date.now()` 时间戳 + `requestAnimationFrame` 逐帧对账 + 定时到点触发，**切到后台标签页也不掉线、不累积误差** |
| ⏸️ 暂停 / 继续 | 暂停时保留已进行的时长，继续后接着走，不会归零 |
| 🛑 二次确认放弃 | 点“放弃”会弹出确认框，并以随机劝说话术再劝你一次（10 条语料） |
| 📊 进度条 | 实时反映已完成比例 |
| 🏷️ 标签页标题 | 每秒同步剩余时间到浏览器标题，切窗口也能一眼看到还剩多久 |
| 💬 每分钟鼓励语 | 内置 110 条鼓励语料，每分钟随机显示一条，并避免短期内重复 |
| ⏰ 里程碑提醒 | 剩余 30 秒 / 10 秒时自动提示 |
| 🔔 到点铃声 | Web Audio API 实时合成旋律（C5–E5–G5–C6 上行琶音循环 + 长尾音，约 6 秒），**无需任何音频文件** |
| 🔇 铃声开关 | 右上角苹果风格开关，一键静音，状态本地记忆 |
| 🎉 完成庆祝 | 撒彩纸动画 + “太棒了”文案提示 |
| 🌗 亮 / 暗双主题 | 默认跟随系统 `prefers-color-scheme`，也可手动切换并记忆 |
| 🌈 白天场景 | 太阳、飘动的云朵、星光，以及**每分钟划出一道彩虹**（5s 划出 → 10s 停留 → 5s 反向收回） |
| 🌙 夜晚场景 | 月亮、随机星空、3 条以 850px/s 飞过的流星 |
| 👆 装饰互动 | 点击太阳 / 月亮 / 云朵会有弹跳动效 |
| ⌨️ 快捷键 | 空格开始、P 键暂停、Esc 放弃，纯键盘也能操作 |
| 💾 本地记忆 | 主题与铃声开关存入 `localStorage`，下次打开保持习惯 |

---

## 🚀 快速开始

1. 下载本仓库；
2. **双击 `index.html`**，即可在浏览器中打开（推荐 Edge / Chrome 等 Chromium 内核浏览器）；
3. 输入专注分钟数，点“开始”，进入心流。

> 无需安装、无需联网、无需构建，单个 HTML 文件即完整可用。

### ⌨️ 快捷键

| 按键 | 作用 |
| --- | --- |
| `空格` | 开始 / 放弃当前专注 |
| `P` | 暂停 / 继续 |
| `Esc` | 开始 / 放弃当前专注 |

---

## 🗂 文件结构

```
Study-Focus-Countdown/
├── index.html                  # 主程序：学习专注倒计时（单文件，V2.4 beta）
├── 学习倒计时提示语管理工具.pyw    # 配套工具：图形化管理页面里的鼓励语
├── 启动提示语管理工具.vbs         # 配套工具：静默启动器（无控制台窗口）
├── README.md
└── LICENSE
```

---

## 🛠 提示语管理工具

嫌内置的 110 条鼓励语不合口味？可以用配套的图形化工具自己改。

**能做什么**

- 自动识别同目录下的倒计时页面，解析其中“每分钟显示一次”的鼓励语库（`quotes` 数组）；
- 以列表方式浏览、添加、修改、删除鼓励语，**每次操作立即写回页面文件**，刷新页面即可生效；
- 支持配置启动时申请管理员权限（UAC），也可一键立即提权（用于写回权限受限的目录）；
- 仅使用 Python 标准库（`tkinter` / `ctypes` / `re` / `json` / `os`），无需安装任何第三方依赖。

**怎么用**

1. 确保已安装 Python 3（标准安装自带 `pythonw.exe`）；
2. 把 `学习倒计时提示语管理工具.pyw`、`启动提示语管理工具.vbs` 与倒计时页面放在**同一个文件夹**；
3. 双击 `启动提示语管理工具.vbs` 静默启动（无黑框窗口）；
4. 修改后保存，回到页面刷新一下就行。

> 配置保存在同目录的 `countdown_tool_settings.json`（自动生成，无需手动编辑，也不会提交到仓库）。

---

## ⚙️ 实现要点

- **时间戳驱动**：整轮倒计时以“结束时间戳”为唯一真相，显示值每帧由墙钟重算，因此后台节流、系统挂起都不会造成计时偏差；
- **多重触发兜底**：到点完成由 `setTimeout` 精确定时 + 每秒 `setInterval` + 前台 `rAF` 三路兜底，谁先到谁执行，且执行是幂等的；
- **音频保活**：借助静音的 `AudioBufferSourceNode` 循环，改善后台标签页的铃声播放；回到前台时自动恢复被浏览器挂起的 `AudioContext`；
- **纯合成音效**：铃声全部由振荡器 + 音量包络实时合成，音频文件为 0 字节；
- **纯 CSS 场景动画**：太阳、云、星空、流星、彩虹均为 CSS 动画与少量 DOM 计算，无任何图片资源；
- **彩虹的整分钟复位**：彩虹的存续由每秒 tick 校正，保证后台跨分钟时不会漏掉下一次触发。

---

## 🌐 浏览器兼容

- Microsoft Edge / Google Chrome / 其他 Chromium 内核浏览器（推荐）；
- 已针对 Chromium 的后台节流行为与自动播放策略做适配；
- 提示：浏览器要求**用户先有一次交互**才允许播放声音，所以铃声会在你点击“开始”之后才具备播放条件。

---

## 🤝 贡献

欢迎提 Issue 或 PR：新增鼓励语、优化装饰动画、适配更多浏览器都可以。

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源，可自由使用、修改与分发。

---

## English Summary

**Study Focus Countdown** is a single-file, dependency-free HTML timer that helps you get into a flow state while studying. It features timestamp-accurate countdown that keeps running in background tabs, per-minute motivational quotes (110 built-in), 30s/10s milestone reminders, a Web Audio synthesized chime (no audio files), confetti celebration, light/dark themes following your system, and animated day/night scenery with a rainbow drawn every minute. Just open `index.html` — that's it. A companion Tkinter tool (`学习倒计时提示语管理工具.pyw`) is included for managing the quote library. Licensed under MIT.
