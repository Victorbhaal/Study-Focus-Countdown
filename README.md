# 学习专注倒计时 / Study Focus Countdown

学习时能帮你快速进入状态的倒计时工具。
A countdown timer that helps you get into the zone while studying.

单文件 HTML，不用装任何依赖，也不用联网。双击打开就能用。白天页面里有太阳、云朵、彩虹，晚上切换到月亮、星空、流星。每分钟随机弹一句鼓励的话，倒计时结束用合成的铃声提醒你该休息了。
A single HTML file. No dependencies, no build step, no internet required. Just double-click and go. Day mode has a sun, clouds, and a rainbow. Night mode swaps to a moon, stars, and shooting stars. Each minute you spend focused, a random encouragement pops up. When the timer ends, a synthesized chime tells you it's break time.

---

## 功能

| 功能 | 说明 |
| --- | --- |
| 🕐 自定义时长 | 输入 1–180 分钟，默认 25 分钟 |
| ⏱️ 高精度计时 | 基于 `Date.now()` 时间戳 + `requestAnimationFrame` 逐帧对账，**切到后台标签页也不掉线** |
| ⏸️ 暂停 / 继续 | 暂停时保留已进行的时长，继续接着走，不会归零 |
| 🛑 二次确认放弃 | 点"放弃"会弹出确认框，还会随机挑一条劝说话术再劝你一次 |
| 📊 进度条 | 实时反映已完成比例 |
| 🏷️ 标签页标题 | 每秒同步剩余时间到浏览器标题，切窗口也能一眼看到还剩多久 |
| 💬 每分钟鼓励语 | 内置 110 条，每分钟随机显示一条，不会短期内重复 |
| ⏰ 里程碑提醒 | 剩余 30 秒 / 10 秒时自动提示 |
| 🔔 到点铃声 | 用 Web Audio API 实时合成旋律，**不需要任何音频文件** |
| 🔇 铃声开关 | 右上角苹果风格开关，一键静音，状态本地记忆 |
| 🎉 完成庆祝 | 撒彩纸动画 + "太棒了"提示 |
| 🌗 亮 / 暗双主题 | 默认跟随系统，也可手动切换并记忆 |
| 🌈 白天场景 | 太阳、飘动的云朵、星光，**每分钟划出一道彩虹** |
| 🌙 夜晚场景 | 月亮、随机星空、流星 |
| 👆 装饰互动 | 点击太阳 / 月亮 / 云朵会有弹跳动画 |
| ⌨️ 快捷键 | 空格开始、P 键暂停、Esc 放弃 |
| 💾 本地记忆 | 主题与铃声开关存入 `localStorage` |

---

## 快速开始

把仓库克隆下来，双击 `index.html`，用 Edge 或 Chrome 打开就行。填个分钟数，点"开始"。

> 不用安装、不用联网、不用构建，单个 HTML 文件即完整可用。

### 快捷键

| 按键 | 作用 |
| --- | --- |
| `空格` | 开始 / 放弃当前专注 |
| `P` | 暂停 / 继续 |
| `Esc` | 开始 / 放弃当前专注 |

---

## 文件结构

```
Study-Focus-Countdown/
├── index.html                  # 主程序：学习专注倒计时（单文件，V2.4 beta）
├── 学习倒计时提示语管理工具.pyw    # 配套工具：图形化管理页面里的鼓励语
├── README.md
└── LICENSE
```

---

## 提示语管理工具

内置的 110 条鼓励语你觉得不够用？用这个工具自己改。

**能做什么**

- 自动识别同目录下的倒计时页面，解析其中每分钟显示的鼓励语库（`quotes` 数组）；
- 以列表方式浏览、添加、修改、删除鼓励语，每次操作写回页面文件，刷新页面即生效；
- 支持配置启动时申请管理员权限（UAC），也可一键立即提权（用于写回权限受限的目录）；
- 只使用 Python 标准库（`tkinter` / `ctypes` / `re` / `json` / `os`），不装第三方依赖。

**怎么用**

1. 确保已安装 Python 3（标准安装自带 `pythonw.exe`）；
2. 把 `学习倒计时提示语管理工具.pyw` 和倒计时页面放在同一个文件夹；
3. 双击 `.pyw` 文件启动；
4. 修改后保存，回到页面刷新一下就行。

配置保存在同目录的 `countdown_tool_settings.json`（自动生成，不提交到仓库）。

---

## 实现细节

计时器用"结束时间戳"作为唯一真相，显示值每帧由墙钟重算。这样后台标签页被节流了也不会累积误差。到点完成用了三路兜底：`setTimeout` 精确定时、每秒 `setInterval`、前台 `rAF` 逐帧对账——谁先到谁执行，执行是幂等的。

铃声全部用振荡器加音量包络实时合成，不需要任何音频文件。白天/夜晚的场景动画全是 CSS 动画加少量 DOM 计算，没有图片资源。彩虹的存续靠每秒 tick 校正，保证后台跨分钟时不会漏掉触发。

音频保活方面，后台用静音的 `AudioBufferSourceNode` 循环改善铃声播放；回到前台时自动恢复被浏览器挂起的 `AudioContext`。浏览器要求用户先有一次交互才允许播放声音，所以铃声会在你点击"开始"之后才具备播放条件。

---

## 浏览器兼容

- Edge / Chrome 等 Chromium 内核浏览器（推荐）
- 已针对 Chromium 的后台节流行为与自动播放策略做适配
- 提示：浏览器要求用户先有一次交互才允许播放声音，所以铃声会在你点击"开始"之后才具备播放条件

---

## 参与贡献

欢迎提 Issue 或 PR。新增鼓励语、优化装饰动画、适配更多浏览器都可以。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源，可自由使用、修改与分发。

---

## English Summary

**Study Focus Countdown** is a single-file, dependency-free HTML timer. It uses timestamp-accurate countdown that keeps running in background tabs, per-minute motivational quotes (110 built-in), 30s/10s milestone reminders, a Web Audio synthesized chime (no audio files), confetti celebration, light/dark themes, and animated day/night scenery with a rainbow drawn every minute. Just open `index.html` — that's it. A companion Tkinter tool (`学习倒计时提示语管理工具.pyw`) is included for managing the quote library. Licensed under MIT.
