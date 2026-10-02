# -*- coding: utf-8 -*-
# TIPS_TOOL_MARKER  <-- 启动器(启动提示语管理工具.vbs)据此识别本文件，请勿删除。
"""
学习倒计时提示语管理工具
========================
与学习倒计时页面（学习倒计时*.html）放在同一个文件夹根目录下即可使用。

功能：
  1. 自动识别同目录下的学习倒计时页面，解析“每分钟显示一次”的鼓励语语料库（quotes 数组）。
  2. 支持对语料库进行：添加、修改、删除；每次操作立即写回页面文件，刷新页面即生效。
  3. 可配置启动时弹出“以管理员身份运行”的 UAC 提权界面；也可一键立即提权。

说明：
  - 只管理“每分钟显示一次”的鼓励语（quotes）；
    “放弃弹窗的提示语”（giveUpTips）与固定文案（还剩30秒/最后10秒等）不受影响。
  - 仅使用 Python 标准库（tkinter / ctypes / re / json / os），无需安装任何依赖。

配置保存在同目录的 countdown_tool_settings.json（自动生成）。
"""

import ctypes
import json
import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(TOOL_DIR, "countdown_tool_settings.json")


# ----------------------------------------------------------------------------
# 提权（UAC）
# ----------------------------------------------------------------------------
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    """通过 runas 以管理员身份重新启动自身，返回是否已发起提权。"""
    script = os.path.abspath(__file__)
    params = '"%s"' % script
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    except Exception:
        ret = 0
    return ret > 32


# ----------------------------------------------------------------------------
# 配置文件
# ----------------------------------------------------------------------------
def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg = data
    except Exception:
        pass
    cfg.setdefault("auto_elevate", False)
    cfg.setdefault("last_file", None)
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ----------------------------------------------------------------------------
# 解析 / 序列化 quotes 语料库
# ----------------------------------------------------------------------------
def find_quotes_block(text):
    """定位 `const quotes = [ ... ];` 整块。

    返回 (block_start, block_end)（block_end 指向 ';' 之后），找不到返回 (None, None)。
    逐字符扫描以正确跳过字符串字面量内的引号/括号/转义。
    """
    m = re.search(r"const\s+quotes\s*=\s*\[", text)
    if not m:
        return None, None
    block_start = m.start()
    i = m.end() - 1  # 指向 '[' 字符
    depth = 0
    in_string = False
    escaped = False
    n = len(text)
    while i < n:
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    j = i + 1
                    while j < n and text[j] in " \t\r\n":
                        j += 1
                    if j < n and text[j] == ";":
                        i = j
                    return block_start, i + 1
        i += 1
    return block_start, None


def parse_entries(block_text):
    """从语料库整块文本中提取全部字符串条目（自动跳过声明、逗号、空白、括号）。"""
    entries = []
    n = len(block_text)
    i = 0
    while i < n:
        if block_text[i] == '"':
            j = i + 1
            buf = []
            while j < n:
                c = block_text[j]
                if c == "\\":
                    if j + 1 < n:
                        nxt = block_text[j + 1]
                        if nxt == "n":
                            buf.append("\n")
                        elif nxt == "r":
                            buf.append("\r")
                        elif nxt == "t":
                            buf.append("\t")
                        elif nxt == "\\":
                            buf.append("\\")
                        elif nxt == '"':
                            buf.append('"')
                        else:
                            buf.append(nxt)
                        j += 2
                        continue
                elif c == '"':
                    break
                else:
                    buf.append(c)
                j += 1
            entries.append("".join(buf))
            i = j + 1
        else:
            i += 1
    return entries


def serialize_quotes(entries, indent):
    """按统一格式重建 `const quotes = [...]` 整块（每条单独一行）。

    注意：`indent` 是原文件中 `const quotes` 所在行的行首缩进；
    块的开头 `const quotes = [` 本身不加缩进（该行行首缩进仍保留在
    text[:block_start] 中），仅内部条目与收尾 `];` 用缩进对齐。
    """
    inner = indent + "    "
    lines = ["const quotes = ["]
    for e in entries:
        esc = e.replace("\\", "\\\\").replace('"', '\\"')
        esc = esc.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        lines.append(inner + '"' + esc + '",')
    lines.append(indent + "];")
    # 注意：不以换行结尾 —— 原文件 `];` 后的换行仍保留在 text[block_end:] 中，
    # 避免多出一行空行。
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# 自动识别同目录下的学习倒计时页面
# ----------------------------------------------------------------------------
def find_countdown_files():
    """返回同目录下疑似学习倒计时页面的【完整路径】列表（按相关度+时间排序）。

    识别依据（满足其一即可）：
      - 文件名含“倒计时”（旧命名习惯）；
      - 文件内容含语料库标记 `const quotes = [`（对改名后的文件也能识别，
        如 V2.4bate.html；其它无关 html 如 mario/florr/qr 均不含该标记）。
    """
    candidates = []
    try:
        for name in os.listdir(TOOL_DIR):
            if not name.lower().endswith(".html"):
                continue
            path = os.path.join(TOOL_DIR, name)
            if "倒计时" in name:
                candidates.append(path)
                continue
            # 按内容标记识别（读取开头一段即可）
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(65536)
            except Exception:
                continue
            if re.search(r"const\s+quotes\s*=\s*\[", head):
                candidates.append(path)
    except Exception:
        pass

    def rank(path):
        name = os.path.basename(path)
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            mtime = 0
        return (1 if "学习" in name else 0, mtime)

    candidates.sort(key=rank, reverse=True)
    return candidates


# ----------------------------------------------------------------------------
# 主界面
# ----------------------------------------------------------------------------
class App:
    def __init__(self, cfg):
        self.cfg = cfg
        self.current_file = None      # 当前页面绝对路径（可能在目录外）
        self.entries = []
        self._files = []              # 下拉框选项：完整路径列表
        self._label_to_path = {}      # 下拉框显示名 -> 完整路径

        self.root = tk.Tk()
        self.root.title("学习倒计时 · 提示语管理工具")
        self.root.geometry("720x600")
        self.root.minsize(600, 460)

        # 字体
        font_ui = ("Microsoft YaHei UI", 10)
        self.root.option_add("*Font", font_ui)

        self._build_ui()

        self.refresh_candidates()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # ---------- 界面搭建 ----------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}

        # 顶部：文件选择
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 2))

        tk.Label(top, text="倒计时文件：").pack(side="left")
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(top, textvariable=self.file_var, state="readonly", width=30)
        self.file_combo.pack(side="left", padx=(2, 6))
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_changed)

        tk.Button(top, text="重新扫描", command=self.rescan).pack(side="left", padx=2)
        tk.Button(top, text="选择文件…", command=self.browse_file).pack(side="left", padx=2)
        tk.Button(top, text="打开倒计时页面", command=self.open_page).pack(side="left", padx=2)

        # 语料库说明
        info = tk.Frame(self.root)
        info.pack(fill="x", **pad)
        self.count_label = tk.Label(info, text="已识别 0 条提示语（每分钟显示一次）",
                                    font=("Microsoft YaHei UI", 10, "bold"))
        self.count_label.pack(side="left")
        tk.Label(info, text="　（放弃弹窗提示语不在此列，不受影响）",
                 fg="#8a6f5c").pack(side="left")

        # 中部：列表
        mid = tk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=10, pady=4)
        self.listbox = tk.Listbox(mid, font=("Microsoft YaHei UI", 10),
                                  activestyle="dotbox", exportselection=False)
        sb = tk.Scrollbar(mid, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda e: self.edit_entry())
        self.listbox.bind("<Delete>", lambda e: self.delete_entry())

        # 操作按钮
        ops = tk.Frame(self.root)
        ops.pack(fill="x", padx=10, pady=6)
        tk.Button(ops, text="＋ 添加", width=12, command=self.add_entry).pack(side="left", padx=4)
        tk.Button(ops, text="✎ 修改", width=12, command=self.edit_entry).pack(side="left", padx=4)
        tk.Button(ops, text="🗑 删除", width=12, command=self.delete_entry).pack(side="left", padx=4)
        tk.Label(ops, text="双击条目可直接修改　·　Delete 键可删除",
                 fg="#8a6f5c").pack(side="left", padx=10)

        # 提权设置
        priv = tk.Frame(self.root)
        priv.pack(fill="x", padx=10, pady=4)
        self.auto_elevate_var = tk.BooleanVar(value=bool(self.cfg.get("auto_elevate")))
        tk.Checkbutton(priv, text="启动时以管理员身份运行（弹出 UAC 提权界面）",
                       variable=self.auto_elevate_var, command=self.on_toggle_elevate).pack(side="left")
        tk.Button(priv, text="立即提权运行", command=self.elevate_now).pack(side="left", padx=10)

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                          relief="sunken", bd=1, padx=6, pady=3)
        status.pack(fill="x", side="bottom")

    # ---------- 文件 / 语料库 ----------
    def set_status(self, s):
        self.status_var.set(s)

    def load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror("无法读取", "无法读取文件：%s\n%s" % (path, e))
            return False

        block_start, block_end = find_quotes_block(text)
        if block_start is None or block_end is None:
            messagebox.showerror("未识别",
                                 "未在文件中找到语料库（const quotes = [...]），\n"
                                 "该文件可能不是学习倒计时页面。")
            return False

        self.entries = parse_entries(text[block_start:block_end])
        self.current_file = path
        # 立即持久化完整路径：下次启动自动恢复，无需重新选择
        self.cfg["last_file"] = os.path.abspath(path)
        save_config(self.cfg)
        self.refresh_list()
        self.set_status("已载入：%s　共 %d 条提示语" % (os.path.basename(path), len(self.entries)))
        return True

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, e in enumerate(self.entries, 1):
            self.listbox.insert(tk.END, "%d. %s" % (i, e))
        self.count_label.config(text="已识别 %d 条提示语（每分钟显示一次）" % len(self.entries))

    def save(self):
        """将当前 entries 写回文件（原子写入 + 往返校验）。"""
        if not self.current_file:
            return False
        try:
            with open(self.current_file, "r", encoding="utf-8", newline="") as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror("无法读取", "无法读取文件：%s" % e)
            return False

        block_start, block_end = find_quotes_block(text)
        if block_start is None or block_end is None:
            messagebox.showerror("未识别", "无法定位语料库，未保存。")
            return False

        line_start = text.rfind("\n", 0, block_start) + 1
        indent = text[line_start:block_start]
        serialized = serialize_quotes(self.entries, indent)
        new_text = text[:block_start] + serialized + text[block_end:]

        # 往返校验：写入后的语料库条数必须一致
        bs2, be2 = find_quotes_block(new_text)
        if bs2 is None or be2 is None or len(parse_entries(new_text[bs2:be2])) != len(self.entries):
            messagebox.showerror("校验失败", "写入校验未通过，未保存。")
            return False

        tmp = self.current_file + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)
            os.replace(tmp, self.current_file)
        except PermissionError:
            self._cleanup_tmp(tmp)
            messagebox.showerror("写入失败",
                                 "无法写入文件，可能正被浏览器或编辑器占用。\n"
                                 "请关闭占用该文件的程序后重试。")
            return False
        except Exception as e:
            self._cleanup_tmp(tmp)
            messagebox.showerror("写入失败", "保存出错：%s" % e)
            return False

        self.set_status("已保存，共 %d 条 · 刷新学习倒计时页面即可生效" % len(self.entries))
        return True

    @staticmethod
    def _cleanup_tmp(tmp):
        try:
            os.remove(tmp)
        except Exception:
            pass

    # ---------- 文件选择（全程使用完整路径）----------
    @staticmethod
    def _resolve_saved_file(value):
        """把配置里保存的值解析为完整路径；兼容旧版本只存文件名的情况。"""
        if not value:
            return None
        if os.path.isabs(value):
            return value if os.path.exists(value) else None
        p = os.path.join(TOOL_DIR, value)
        return p if os.path.exists(p) else None

    def _rebuild_file_combo(self):
        """根据 self._files（完整路径列表）重建下拉框选项。

        显示名默认取文件名；若同目录/跨目录出现重名，则用完整路径作显示名兜底。
        """
        self._label_to_path = {}
        labels = []
        for p in self._files:
            label = os.path.basename(p)
            if label in self._label_to_path:
                label = p  # 重名兜底
            k = 2
            while label in self._label_to_path:
                label = "%s (%d)" % (os.path.basename(p), k)
                k += 1
            self._label_to_path[label] = p
            labels.append(label)
        self.file_combo["values"] = labels

    def _set_selection(self, path):
        """将下拉框选中值设为 path 对应的显示名；path 为空则清空。"""
        if not path:
            self.file_var.set("")
            return
        for label, p in self._label_to_path.items():
            if p == path:
                self.file_var.set(label)
                return
        self.file_var.set("")

    def refresh_candidates(self):
        """启动 / 重新扫描：汇总可用文件，并恢复到上次使用的文件。

        候选来源 = 自动扫描 + 上次保存的路径(存在即优先) + 当前已选文件。
        只要上次/当前文件仍然存在，就绝不无故清空选择。
        """
        # 1. 汇总候选（完整路径，去重）
        paths = find_countdown_files()
        for p in (self._resolve_saved_file(self.cfg.get("last_file")),
                  self.current_file):
            if p and p not in paths and os.path.exists(p):
                paths.insert(0, p)
        self._files = paths
        self._rebuild_file_combo()

        # 2. 决定要加载的文件：优先上次路径，其次当前文件，再次最优候选
        target = None
        for p in (self._resolve_saved_file(self.cfg.get("last_file")),
                  self.current_file):
            if p and os.path.exists(p):
                target = p
                break
        if target is None and paths:
            target = paths[0]

        # 3. 加载或清空
        if target is None:
            self.current_file = None
            self.entries = []
            self._set_selection(None)
            self.refresh_list()
            self.set_status("未找到学习倒计时页面（同目录 *.html 且文件名含“倒计时”），"
                            "可点击“选择文件…”手动指定")
            return
        if target != self.current_file:
            self.load_file(target)
            self._set_selection(target)
        else:
            self._set_selection(target)
            self.set_status("已载入：%s　共 %d 条提示语"
                            % (os.path.basename(target), len(self.entries)))

    def on_file_changed(self, _event=None):
        label = self.file_var.get()
        path = self._label_to_path.get(label)
        if path and path != self.current_file:
            self.load_file(path)

    def rescan(self):
        self.refresh_candidates()
        if self.current_file:
            self.set_status("已重新扫描目录，当前文件：%s"
                            % os.path.basename(self.current_file))
        else:
            self.set_status("已重新扫描目录")

    def browse_file(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="选择学习倒计时页面",
            filetypes=[("HTML 文件", "*.html"), ("所有文件", "*.*")],
            initialdir=TOOL_DIR)
        if not path:
            return
        if self.load_file(path):
            # 加入下拉框并选中（load_file 已持久化完整路径）
            if path not in self._files:
                self._files.insert(0, path)
                self._rebuild_file_combo()
            self._set_selection(path)

    def open_page(self):
        if not self.current_file:
            messagebox.showwarning("未选择文件", "请先选择学习倒计时文件。")
            return
        try:
            os.startfile(self.current_file)
        except Exception as e:
            messagebox.showerror("无法打开", str(e))

    # ---------- 增 / 改 / 删 ----------
    def ask_text(self, title, initial=""):
        """模态输入框；返回新文本，取消返回 None。"""
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="提示语内容：").pack(padx=14, pady=(14, 4), anchor="w")
        txt = tk.Text(dlg, width=52, height=3, font=("Microsoft YaHei UI", 11), wrap="word")
        txt.pack(padx=14, pady=4)
        if initial:
            txt.insert("1.0", initial)

        result = {"value": None}

        def on_ok():
            v = txt.get("1.0", "end").strip()
            v = re.sub(r"\s+", " ", v)   # 折叠换行/多余空白为单个空格
            if not v:
                messagebox.showwarning("内容为空", "请输入提示语内容。", parent=dlg)
                return
            result["value"] = v
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btn_row = tk.Frame(dlg)
        btn_row.pack(pady=(4, 14))
        tk.Button(btn_row, text="确定", width=10, command=on_ok).pack(side="left", padx=6)
        tk.Button(btn_row, text="取消", width=10, command=on_cancel).pack(side="left", padx=6)
        dlg.bind("<Escape>", lambda e: on_cancel())
        dlg.bind("<Return>", lambda e: on_ok())
        dlg.bind("<Control-Return>", lambda e: on_ok())
        txt.focus_set()
        if initial:
            txt.tag_add("sel", "1.0", "end")

        self.root.wait_window(dlg)
        return result["value"]

    def _require_file(self):
        if not self.current_file:
            messagebox.showwarning("未选择文件", "请先选择学习倒计时文件。")
            return False
        return True

    def add_entry(self):
        if not self._require_file():
            return
        v = self.ask_text("添加提示语")
        if v is None:
            return
        self.entries.append(v)
        if self.save():
            self.refresh_list()
            idx = len(self.entries) - 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)

    def edit_entry(self):
        if not self._require_file():
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("未选择", "请先在列表中选择要修改的提示语。")
            return
        idx = sel[0]
        v = self.ask_text("修改提示语", initial=self.entries[idx])
        if v is None:
            return
        self.entries[idx] = v
        if self.save():
            self.refresh_list()
            self.listbox.selection_set(idx)
            self.listbox.see(idx)

    def delete_entry(self):
        if not self._require_file():
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("未选择", "请先在列表中选择要删除的提示语。")
            return
        idx = sel[0]
        if len(self.entries) <= 1:
            messagebox.showwarning("无法删除",
                                   "至少需要保留一条提示语，否则倒计时页面无法正常轮换。")
            return
        if not messagebox.askyesno("确认删除",
                                   "确定删除第 %d 条提示语？\n\n%s" % (idx + 1, self.entries[idx])):
            return
        del self.entries[idx]
        if self.save():
            self.refresh_list()
            if idx < len(self.entries):
                self.listbox.selection_set(idx)
                self.listbox.see(idx)

    # ---------- 提权 ----------
    def on_toggle_elevate(self):
        self.cfg["auto_elevate"] = bool(self.auto_elevate_var.get())
        save_config(self.cfg)
        if self.auto_elevate_var.get():
            self.set_status("已开启启动提权：下次启动将弹出“以管理员身份运行”的 UAC 界面")
        else:
            self.set_status("已关闭启动提权")

    def elevate_now(self):
        if is_admin():
            messagebox.showinfo("已提权", "当前程序已处于管理员权限。")
            return
        if relaunch_as_admin():
            self.root.destroy()
        else:
            messagebox.showwarning("提权取消", "未获得管理员权限，继续以普通权限运行。")


# ----------------------------------------------------------------------------
# 入口
# ----------------------------------------------------------------------------
def setup_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    setup_dpi()
    cfg = load_config()
    if cfg.get("auto_elevate") and not is_admin():
        if relaunch_as_admin():
            sys.exit(0)  # 已弹 UAC，提权后的新实例会重新启动本程序
        # 用户取消/提权失败 → 继续以普通权限运行
    app = App(cfg)
    app.root.mainloop()


if __name__ == "__main__":
    main()
