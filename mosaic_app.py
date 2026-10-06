import json
import os
import re
import sys
import tkinter as tk
import ctypes
from tkinter import filedialog, messagebox
from tkinter import ttk

from PIL import Image, ImageDraw, ImageOps, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

MOSAIC_GRIDS = [16, 24, 32, 48, 64, 96, 128]
GRID_NATIVE = "native"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff")

APP_NAME = "Pixelate"
ICON_NAME = "icon.ico"
SETTINGS_FILE = "settings.json"
HISTORY_LIMIT = 50
MAX_PREVIEW_PIXELS = 4_000_000
GRID_LINE_LIMIT = 600
ERASED_PATTERN_BUDGET = 240
ERASED_CHECKER_PX = 7
PALETTE_SIZE = 8
FIXED_COLORS = ["#FFC700", "#FFFFFF", "#9E9E9E", "#4A4A4A", "#000000"]
DEFAULT_NAME_TEMPLATE = "{原名}_马赛克_{倍率}"
NAME_HINT = "占位符 {原名} {序号} {总数} {倍率}"
NAME_HINT_MANY = "占位符 {原名} {序号} {总数} {倍率}；应用到全部按各自图片展开"
_ILLEGAL_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

LIGHT = {
    "bg": "#FFFFFF",
    "surface": "#EBEBEB",
    "border": "#E3E3E3",
    "border_active": "#C9C9C9",
    "ink": "#1A1A1A",
    "muted": "#6B6B6B",
    "disabled": "#A3A3A3",
    "accent": "#FFC700",
    "accent_hover": "#F0B800",
    "accent_pressed": "#E0A800",
    "accent_disabled": "#F2ECD6",
    "on_accent": "#1A1A1A",
    "button_hover": "#EBEBEB",
    "button_pressed": "#E0E0E0",
    "canvas": "#1C1C1C",
    "canvas_text": "#9E9E9E",
    "canvas_hint": "#CCCCCC",
    "grid_line": "#000000",
    "knob": "#BFBFBF",
    "knob_on": "#FFFFFF",
}

DARK = {
    "bg": "#1C1C1C",
    "surface": "#242424",
    "border": "#2E2E2E",
    "border_active": "#3D3D3D",
    "ink": "#EDEDED",
    "muted": "#8C8C8C",
    "disabled": "#5A5A5A",
    "accent": "#FFC700",
    "accent_hover": "#F0B800",
    "accent_pressed": "#E0A800",
    "accent_disabled": "#3F3A22",
    "on_accent": "#1A1A1A",
    "button_hover": "#2E2E2E",
    "button_pressed": "#383838",
    "canvas": "#0E0E0E",
    "canvas_text": "#6E6E6E",
    "canvas_hint": "#7A7A7A",
    "grid_line": "#FFFFFF",
    "knob": "#4A4A4A",
    "knob_on": "#FFFFFF",
}

UI_FONT = ("Microsoft YaHei UI", 10)
LABEL_FONT = ("Microsoft YaHei UI", 9)
TITLE_FONT = ("Microsoft YaHei UI", 9, "bold")


def build_theme(root, c):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=c["bg"], foreground=c["ink"], font=LABEL_FONT)
    style.configure("TFrame", background=c["bg"])
    style.configure("TLabel", background=c["bg"], foreground=c["ink"])
    style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"])
    style.configure("Status.TLabel", background=c["surface"], foreground=c["muted"], padding=(10, 5))
    style.configure("Panel.TFrame", background=c["surface"])
    style.configure("Panel.TLabel", background=c["surface"], foreground=c["ink"])
    style.configure("Panel.Muted.TLabel", background=c["surface"], foreground=c["muted"])
    style.configure(
        "Panel.TCheckbutton",
        background=c["surface"],
        foreground=c["ink"],
        font=LABEL_FONT,
    )
    style.map(
        "Panel.TCheckbutton",
        background=[("active", c["surface"])],
        foreground=[("disabled", c["disabled"])],
    )
    style.configure(
        "TLabelframe",
        background=c["bg"],
        bordercolor=c["border"],
        lightcolor=c["border"],
        darkcolor=c["border"],
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=c["bg"],
        foreground=c["ink"],
        font=TITLE_FONT,
    )

    style.configure(
        "TButton",
        background=c["bg"],
        foreground=c["ink"],
        bordercolor=c["border"],
        lightcolor=c["border"],
        darkcolor=c["border"],
        padding=(14, 7),
        font=UI_FONT,
    )
    style.map(
        "TButton",
        background=[
            ("active", c["button_hover"]),
            ("pressed", c["button_pressed"]),
            ("disabled", c["surface"]),
        ],
        foreground=[("disabled", c["disabled"])],
        bordercolor=[("active", c["border_active"])],
    )

    style.configure(
        "Primary.TButton",
        background=c["accent"],
        foreground=c["on_accent"],
        bordercolor=c["accent"],
        lightcolor=c["accent"],
        darkcolor=c["accent"],
        padding=(14, 8),
        font=UI_FONT,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", c["accent_hover"]),
            ("pressed", c["accent_pressed"]),
            ("disabled", c["accent_disabled"]),
        ],
        foreground=[("disabled", c["disabled"])],
    )

    style.configure(
        "Ghost.TButton",
        background=c["surface"],
        foreground=c["muted"],
        bordercolor=c["surface"],
        lightcolor=c["surface"],
        darkcolor=c["surface"],
        padding=(8, 1),
        relief="flat",
        font=LABEL_FONT,
    )
    style.map(
        "Ghost.TButton",
        background=[("active", c["button_hover"]), ("pressed", c["button_pressed"])],
        foreground=[("active", c["ink"])],
        bordercolor=[("active", c["surface"])],
        lightcolor=[("active", c["button_hover"])],
        darkcolor=[("active", c["button_hover"])],
    )

    style.configure(
        "TCombobox",
        background=c["bg"],
        foreground=c["ink"],
        fieldbackground=c["bg"],
        bordercolor=c["border"],
        arrowcolor=c["ink"],
        padding=6,
        font=UI_FONT,
    )
    style.map(
        "TCombobox",
        background=[("active", c["button_hover"])],
        fieldbackground=[("readonly", c["bg"])],
        bordercolor=[("active", c["border_active"])],
        arrowcolor=[("active", c["ink"])],
    )

    style.configure(
        "Tool.TButton",
        background=c["surface"],
        foreground=c["ink"],
        bordercolor=c["border_active"],
        lightcolor=c["border_active"],
        darkcolor=c["border_active"],
        padding=(8, 5),
        font=UI_FONT,
    )
    style.map(
        "Tool.TButton",
        background=[("active", c["button_hover"]), ("pressed", c["button_pressed"])],
        bordercolor=[("active", c["muted"])],
        lightcolor=[("active", c["button_hover"])],
        darkcolor=[("active", c["button_hover"])],
        foreground=[("disabled", c["disabled"])],
    )

    style.configure(
        "Primary.TLabel",
        background=c["surface"],
        foreground=c["ink"],
        font=TITLE_FONT,
    )

    style.configure(
        "Save.TProgressbar",
        background=c["accent"],
        troughcolor=c["border"],
        bordercolor=c["surface"],
        lightcolor=c["accent"],
        darkcolor=c["accent"],
        thickness=6,
    )

    try:
        style.layout("Ghost.TButton", style.layout("TButton"))
        style.layout("Tool.TButton", style.layout("TButton"))
        style.layout("Queue.TScrollbar", style.layout("Vertical.TScrollbar"))
        style.layout("Save.TProgressbar", style.layout("Horizontal.TProgressbar"))
    except Exception:
        pass

    style.configure(
        "Queue.TScrollbar",
        background=c["border_active"],
        troughcolor=c["surface"],
        bordercolor=c["surface"],
        lightcolor=c["surface"],
        darkcolor=c["surface"],
        arrowcolor=c["muted"],
        width=12,
        arrowsize=12,
    )
    style.map(
        "Queue.TScrollbar",
        background=[("active", c["muted"])],
        arrowcolor=[("active", c["ink"])],
    )

    style.configure(
        "TEntry",
        fieldbackground=c["bg"],
        foreground=c["ink"],
        bordercolor=c["border"],
        lightcolor=c["border"],
        darkcolor=c["border"],
        insertcolor=c["ink"],
        padding=6,
        font=LABEL_FONT,
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", c["ink"])],
        fieldbackground=[("disabled", c["surface"])],
        foreground=[("disabled", c["disabled"])],
    )
    return style


def render_name_template(template, stem, index=1, total=1, grid=64):
    """把命名模板渲染成实际文件名（不含扩展名）。

    占位符：{原名} {序号} {总数} {倍率}；单张时序号/总数都是 01。
    {倍率} 接受网格数（int 或 (gw, gh)），原分辨率档会写成实际像素尺寸。
    非法文件名字符换成下划线；模板为空或渲染全空时退回原名。
    """
    tpl = (template or "").strip() or DEFAULT_NAME_TEMPLATE
    gw, gh = (int(grid), int(grid)) if isinstance(grid, int) else tuple(grid)
    name = (
        tpl.replace("{原名}", stem)
        .replace("{序号}", f"{index:02d}")
        .replace("{总数}", f"{total:02d}")
        .replace("{倍率}", f"{gw}x{gh}")
    )
    name = _ILLEGAL_NAME_CHARS.sub("_", name).strip().rstrip(". ")
    return name or stem


def grid_dims(mode, size):
    """倍率档位 → 实际网格数 (gw, gh)。native = 原图像素尺寸（1 像素 1 格）。"""
    if mode == GRID_NATIVE:
        return int(size[0]), int(size[1])
    g = int(mode)
    return g, g


def grid_label(mode, size):
    gw, gh = grid_dims(mode, size)
    return f"原分辨率 {gw}x{gh}" if mode == GRID_NATIVE else f"{gw}x{gh}"


def apply_mosaic(img, grid):
    gw, gh = (int(grid), int(grid)) if isinstance(grid, int) else tuple(grid)
    w, h = img.size
    return img.resize((gw, gh), Image.Resampling.NEAREST).resize(
        (w, h), Image.Resampling.NEAREST
    )


def exe_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}({i}){ext}"):
        i += 1
    return f"{base}({i}){ext}"


def settings_path():
    return os.path.join(exe_dir(), SETTINGS_FILE)


def load_theme_pref(default="light"):
    try:
        with open(settings_path(), encoding="utf-8") as f:
            theme = json.load(f).get("theme", default)
    except Exception:
        return default
    return theme if theme in ("light", "dark") else default


def save_theme_pref(name):
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump({"theme": name}, f)
    except Exception:
        pass


class ThemeSwitch(ttk.Frame):
    """Canvas 自绘的滑动开关：开=深色主题。"""

    WIDTH = 46
    HEIGHT = 24
    RADIUS = 11
    KNOB = 8
    STEPS = 8

    def __init__(self, master, text, palette, command):
        super().__init__(master, style="Panel.TFrame")
        self.palette = palette
        self.command = command
        self.on = False
        self._pos = 0.0
        self._from = 0.0
        self._target = 0.0
        self._step = 0
        self._job = None
        self.canvas = tk.Canvas(
            self,
            width=self.WIDTH,
            height=self.HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=palette["surface"],
            cursor="hand2",
        )
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>", self._clicked)
        self.label = ttk.Label(self, text=text, style="Panel.TLabel", cursor="hand2")
        self.label.pack(side=tk.LEFT, padx=(8, 0))
        self.label.bind("<Button-1>", self._clicked)
        self._draw()

    def _clicked(self, event=None):
        self.set_on(not self.on)
        self.command()

    def apply_palette(self, palette):
        self.palette = palette
        self.canvas.config(bg=palette["surface"])
        self._draw()

    def set_on(self, on, animate=True):
        self.on = on
        self._target = 1.0 if on else 0.0
        if not animate:
            if self._job is not None:
                self.canvas.after_cancel(self._job)
                self._job = None
            self._pos = self._target
            self._draw()
            return
        if self._job is not None:
            self.canvas.after_cancel(self._job)
        self._from = self._pos
        self._step = 0
        self._advance()

    def _advance(self):
        self._step += 1
        t = min(self._step / self.STEPS, 1.0)
        self._pos = self._from + (self._target - self._from) * (1 - (1 - t) ** 3)
        self._draw()
        if t < 1.0:
            self._job = self.canvas.after(16, self._advance)
        else:
            self._job = None

    def _draw(self):
        c = self.canvas
        c.delete("all")
        mid = self.HEIGHT / 2
        on = self._pos >= 0.5
        c.create_line(
            self.RADIUS,
            mid,
            self.WIDTH - self.RADIUS,
            mid,
            width=self.HEIGHT - 6,
            capstyle="round",
            fill=self.palette["accent"] if on else self.palette["border"],
        )
        cx = self.RADIUS + (self.WIDTH - 2 * self.RADIUS) * self._pos
        c.create_oval(
            cx - self.KNOB,
            mid - self.KNOB,
            cx + self.KNOB,
            mid + self.KNOB,
            fill=self.palette["knob_on"] if on else self.palette["knob"],
            outline="",
        )


class EditPatch:
    """一次编辑：原图坐标上的矩形，color=None 表示抠成透明。"""

    __slots__ = ("x0", "y0", "x1", "y1", "color")

    def __init__(self, x0, y0, x1, y1, color):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.color = color

    def __repr__(self):
        return f"EditPatch({self.x0},{self.y0},{self.x1},{self.y1},{self.color})"


def apply_patches(img, patches):
    """把覆盖块贴到图上，返回 RGBA。用 ImageDraw 直写像素（不做 alpha 混合）。"""
    out = img if img.mode == "RGBA" else img.convert("RGBA")
    if not patches:
        return out
    draw = ImageDraw.Draw(out)
    w, h = out.size
    for p in patches:
        x0 = max(0, min(p.x0, w))
        y0 = max(0, min(p.y0, h))
        x1 = max(0, min(p.x1, w))
        y1 = max(0, min(p.y1, h))
        if x1 <= x0 or y1 <= y0:
            continue
        draw.rectangle(
            [x0, y0, x1 - 1, y1 - 1],
            fill=(0, 0, 0, 0) if p.color is None else tuple(p.color) + (255,),
        )
    return out


def _rgb_distance(a, b):
    return sum((int(x) - int(y)) ** 2 for x, y in zip(a, b)) ** 0.5


def _rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb[:3])


def _hex_to_rgb(text):
    text = text.lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def has_alpha(img):
    """PNG 透明区（RGBA / LA / 调色板带 transparency）必须保留，否则会被烤成黑块。"""
    if img.mode in ("RGBA", "LA"):
        return True
    return img.mode == "P" and "transparency" in img.info


def extract_palette(img, count=8, min_distance=28, sample=48):
    """从图里取主色：缩到 sample×sample 计数，按占比排序，距离太近的合并掉。

    带透明的图先叠到白底上，否则透明区的黑色会污染调色盘。
    """
    small = img.resize((sample, sample), Image.Resampling.NEAREST)
    if small.mode == "RGBA":
        if small.getchannel("A").getextrema()[0] < 255:
            white = Image.new("RGBA", small.size, (255, 255, 255, 255))
            small = Image.alpha_composite(white, small)
        small = small.convert("RGB")
    else:
        small = small.convert("RGB")
    colors = small.getcolors(sample * sample + 1) or []
    colors.sort(key=lambda pair: -pair[0])
    picked = []
    for _, rgb in colors:
        if all(_rgb_distance(rgb, c) >= min_distance for c in picked):
            picked.append(rgb)
            if len(picked) >= count:
                break
    return picked


def cell_rect(w, h, grid, i, j):
    """第 (i, j) 个马赛克块在原图里的矩形 [x0, y0, x1, y1)。grid 可以是方形数或 (gw, gh)。"""
    gw, gh = (int(grid), int(grid)) if isinstance(grid, int) else tuple(grid)
    x0 = i * w // gw
    y0 = j * h // gh
    return (
        x0,
        y0,
        max(x0 + 1, (i + 1) * w // gw),
        max(y0 + 1, (j + 1) * h // gh),
    )


def render_mosaic(img, grid, patches=()):
    """预览与导出共用的渲染管线：马赛克 → 叠加编辑 → RGBA。"""
    return apply_patches(apply_mosaic(img, grid), patches)


def _short_path(path, keep=2):
    """浮层里只显示末两级目录，免得一条长路径把面板撑满。"""
    parts = os.path.normpath(path).split(os.sep)
    tail = parts[-keep:] if len(parts) > keep else parts
    return ("…\\" + "\\".join(tail)) if len(parts) > keep else path


class QueueItem:
    """待处理队列里的一项：原图 + 各自的命名模板 + 各自的编辑记录。"""

    __slots__ = ("path", "img", "tpl", "patches", "undo", "redo")

    def __init__(self, path, img, tpl):
        self.path = path
        self.img = img
        self.tpl = tpl
        self.patches = []
        self.undo = []
        self.redo = []

    @property
    def stem(self):
        return os.path.splitext(os.path.basename(self.path))[0]

    def rendered(self, index=1, total=1, grid=64):
        return render_name_template(self.tpl, self.stem, index, total, grid)

    def begin_edit(self):
        """一次拖拽只压一条历史：动手前先存当前状态快照。"""
        self.undo.append(list(self.patches))
        if len(self.undo) > HISTORY_LIMIT:
            self.undo.pop(0)
        self.redo.clear()

    def undo_edit(self):
        if not self.undo:
            return False
        self.redo.append(list(self.patches))
        self.patches = self.undo.pop()
        return True

    def redo_edit(self):
        if not self.redo:
            return False
        self.undo.append(list(self.patches))
        self.patches = self.redo.pop()
        return True

    def clear_edits(self):
        self.patches = []


class MosaicApp:
    LIST_ROWS = 5
    TOOLS = (("pan", "平移"), ("pick", "取色"), ("paint", "上色"), ("erase", "抠除"))
    TOOLBAR_W = 172
    SWATCH = 28
    SWATCH_GAP = 5
    SWATCH_COLS = 4
    FIXED_COLS = 3
    SWATCH_BIG = 44

    def __init__(self, root):
        self.root = root
        self.queue = []
        self.index = -1
        self.current_grid = 64
        self.preview_img = None
        self.mosaic_img = None
        self.save_dir = exe_dir()
        self.preview_scale = 1.0
        self.zoom = 1.0
        self.anchor = None
        self.base_scale = 1.0
        self.pan_start = None
        self.anchor_start = None
        self._pending = None
        self._syncing_name = False
        self.tool = "pan"
        self.current_color = (255, 199, 0)
        self._space_down = False
        self._stroke_cells = set()
        self._draw_size = (1, 1)
        self._draw_pos = None
        self._rev = 0
        self._photo_cache = None
        self._swatches = []

        self.dark = load_theme_pref() == "dark"
        self.c = DARK if self.dark else LIGHT

        root.title(APP_NAME)
        root.geometry("1200x720")
        root.minsize(900, 560)
        self.style = build_theme(root, self.c)
        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", self.on_drop)

        main = ttk.Frame(root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.toolbar = ttk.Frame(main, width=self.TOOLBAR_W, style="Panel.TFrame")
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbar.pack_propagate(False)
        self._build_toolbar()

        left = ttk.LabelFrame(main, text="预览")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.canvas = tk.Canvas(left, bg=self.c["canvas"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.canvas.bind("<Configure>", lambda e: self.redraw_preview())
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Double-Button-1>", lambda e: self.reset_zoom())
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_press)
        self.canvas.bind("<B2-Motion>", self.on_middle_motion)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_release)
        self._build_overlay(left)
        root.bind("<KeyPress-space>", self._on_space_down)
        root.bind("<KeyRelease-space>", self._on_space_up)
        root.bind("<Control-z>", lambda e: self.undo_edit())
        root.bind("<Control-Z>", lambda e: self.undo_edit())
        root.bind("<Control-y>", lambda e: self.redo_edit())
        root.bind("<Control-Y>", lambda e: self.redo_edit())
        root.bind("<Control-Shift-Z>", lambda e: self.redo_edit())
        root.bind("<Control-Shift-z>", lambda e: self.redo_edit())

        right = ttk.Frame(main, width=280, style="Panel.TFrame")
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right.pack_propagate(False)

        add_row = ttk.Frame(right, style="Panel.TFrame")
        add_row.pack(fill=tk.X)
        ttk.Button(add_row, text="添加图片...", command=self.pick_image).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        self.clear_btn = ttk.Button(
            add_row, text="清空", command=self.clear_queue, style="Ghost.TButton", width=4
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Label(
            right,
            text="可多选；已加载后再添加会接在后面",
            style="Panel.Muted.TLabel",
        ).pack(anchor=tk.W, pady=(4, 12))

        queue_head = ttk.Frame(right, style="Panel.TFrame")
        queue_head.pack(fill=tk.X)
        self.queue_count = tk.StringVar(value="待处理（0 张）")
        ttk.Label(
            queue_head, textvariable=self.queue_count, style="Panel.TLabel"
        ).pack(side=tk.LEFT)
        self.remove_btn = ttk.Button(
            queue_head, text="删除", command=self.remove_current, style="Ghost.TButton", width=4
        )
        self.remove_btn.pack(side=tk.RIGHT)

        list_row = ttk.Frame(right, style="Panel.TFrame")
        list_row.pack(fill=tk.X, pady=(2, 12))
        self.list_box = tk.Listbox(
            list_row,
            height=self.LIST_ROWS,
            activestyle="none",
            exportselection=False,
            borderwidth=1,
            highlightthickness=0,
            font=LABEL_FONT,
        )
        self.list_scroll = ttk.Scrollbar(
            list_row,
            orient=tk.VERTICAL,
            command=self.list_box.yview,
            style="Queue.TScrollbar",
        )
        self.list_box.config(yscrollcommand=self.list_scroll.set)
        self.list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_box.bind("<<ListboxSelect>>", self._on_list_select)
        self.list_box.bind("<Delete>", lambda e: self.remove_current())
        self.list_box.bind("<Left>", lambda e: self.step(-1))
        self.list_box.bind("<Right>", lambda e: self.step(1))
        self.list_box.bind("<MouseWheel>", self._on_list_wheel)

        ttk.Label(right, text="马赛克倍率（网格数量）", style="Panel.TLabel").pack(
            anchor=tk.W
        )
        self.grid_var = tk.StringVar(value="")
        self.grid_mode = GRID_NATIVE
        self.current_grid = (1, 1)
        self.grid_box = ttk.Combobox(
            right,
            textvariable=self.grid_var,
            state="readonly",
        )
        self.grid_box.pack(fill=tk.X, pady=(2, 6))
        self.grid_box.bind("<<ComboboxSelected>>", self.on_grid_pick)
        self._sync_grid_box()

        self.grid_lines = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right,
            text="显示网格线（仅预览）",
            variable=self.grid_lines,
            command=self.redraw_preview,
            style="Panel.TCheckbutton",
        ).pack(anchor=tk.W, pady=(2, 8))

        ttk.Label(right, text="保存路径", style="Panel.TLabel").pack(
            anchor=tk.W, pady=(6, 0)
        )
        path_row = ttk.Frame(right, style="Panel.TFrame")
        path_row.pack(fill=tk.X, pady=(2, 6))
        self.path_var = tk.StringVar(value=self.save_dir)
        self.path_entry = ttk.Entry(path_row, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_row, text="浏览", command=self.browse_save_dir).pack(
            side=tk.RIGHT, padx=(4, 0)
        )

        name_head = ttk.Frame(right, style="Panel.TFrame")
        name_head.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(name_head, text="输出文件名", style="Panel.TLabel").pack(side=tk.LEFT)
        self.name_reset_btn = ttk.Button(
            name_head, text="默认", command=self.reset_current_name,
            style="Ghost.TButton", width=4,
        )
        self.name_reset_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.apply_all_btn = ttk.Button(
            name_head, text="应用到全部", command=self.apply_name_to_all,
            style="Ghost.TButton", width=9,
        )
        self.apply_all_btn.pack(side=tk.RIGHT)
        self.name_var = tk.StringVar(value=DEFAULT_NAME_TEMPLATE)
        ttk.Entry(right, textvariable=self.name_var).pack(fill=tk.X, pady=(2, 4))
        self.name_preview = ttk.Label(
            right, text="", style="Panel.Muted.TLabel", anchor=tk.W, wraplength=248
        )
        self.name_preview.pack(fill=tk.X)
        self.name_hint_var = tk.StringVar(value=NAME_HINT)
        ttk.Label(
            right,
            textvariable=self.name_hint_var,
            style="Panel.Muted.TLabel",
            wraplength=248,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.save_btn = ttk.Button(
            right, text="保存图片", command=self.save_image, style="Primary.TButton"
        )
        self.save_btn.pack(fill=tk.X, pady=(0, 6))

        theme_row = ttk.Frame(right, style="Panel.TFrame")
        theme_row.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        theme_sep = tk.Frame(theme_row, height=1, bg=self.c["border"])
        theme_sep.pack(fill=tk.X, pady=(0, 8))
        self.theme_switch = ThemeSwitch(
            theme_row, "深色模式", self.c, self.toggle_theme
        )
        self.theme_switch.set_on(self.dark, animate=False)
        self.theme_switch.pack(anchor=tk.W)
        self.theme_sep = theme_sep

        self.status = ttk.Label(
            root,
            text="未加载图片",
            anchor=tk.W,
            style="Status.TLabel",
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        self.sep = tk.Frame(root, height=1, bg=self.c["border"])
        self.sep.pack(fill=tk.X, side=tk.BOTTOM)

        self._apply_list_colors()
        self._update_states()
        self._update_edit_state()
        self.name_var.trace_add("write", self._on_name_edited)
        self.root.after_idle(self._style_combobox_popup)

    # ---------- 左侧工具栏 ----------

    def _build_toolbar(self):
        c = self.c
        self.tool_buttons = {}
        for key, label in self.TOOLS:
            btn = ttk.Button(
                self.toolbar,
                text=label,
                command=lambda k=key: self.set_tool(k),
                style="Tool.TButton",
            )
            btn.pack(fill=tk.X, pady=(0, 4))
            self.tool_buttons[key] = btn

        ttk.Label(
            self.toolbar, text="当前色", style="Panel.Muted.TLabel"
        ).pack(anchor=tk.W, pady=(10, 2))
        self.swatch = tk.Canvas(
            self.toolbar,
            width=self.SWATCH_BIG,
            height=self.SWATCH_BIG,
            highlightthickness=1,
            highlightbackground=c["border_active"],
            bd=0,
        )
        self.swatch.pack(anchor=tk.W)
        self.color_label = ttk.Label(
            self.toolbar, text="", style="Panel.Muted.TLabel"
        )
        self.color_label.pack(anchor=tk.W, pady=(2, 10))

        ttk.Label(
            self.toolbar, text="调色盘（本图主色）", style="Panel.Muted.TLabel"
        ).pack(anchor=tk.W, pady=(0, 2))
        pal_w = self.SWATCH_COLS * self.SWATCH + (self.SWATCH_COLS - 1) * self.SWATCH_GAP
        pal_rows = -(-PALETTE_SIZE // self.SWATCH_COLS)
        self.pal_canvas = tk.Canvas(
            self.toolbar,
            width=pal_w,
            height=pal_rows * (self.SWATCH + self.SWATCH_GAP) + 4,
            highlightthickness=0,
            bd=0,
            bg=c["surface"],
        )
        self.pal_canvas.pack(anchor=tk.W)
        self.pal_canvas.bind("<Button-1>", self._on_palette_click)

        ttk.Label(
            self.toolbar, text="固定色板（末位=透明）", style="Panel.Muted.TLabel"
        ).pack(anchor=tk.W, pady=(10, 2))
        fixed = list(FIXED_COLORS) + [None]
        fix_rows = -(-len(fixed) // self.FIXED_COLS)
        self.fix_canvas = tk.Canvas(
            self.toolbar,
            width=self.FIXED_COLS * self.SWATCH + (self.FIXED_COLS - 1) * self.SWATCH_GAP,
            height=fix_rows * (self.SWATCH + self.SWATCH_GAP) + 4,
            highlightthickness=0,
            bd=0,
            bg=c["surface"],
        )
        self.fix_canvas.pack(anchor=tk.W)
        self.fix_canvas.bind("<Button-1>", self._on_fixed_click)

        self.reset_edits_btn = ttk.Button(
            self.toolbar,
            text="还原编辑",
            command=self.reset_edits,
            style="Tool.TButton",
        )
        self.reset_edits_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=(12, 0))
        ttk.Label(
            self.toolbar,
            text="抠掉的格子导出为透明（PNG）",
            style="Panel.Muted.TLabel",
            wraplength=self.TOOLBAR_W - 20,
        ).pack(side=tk.BOTTOM, anchor=tk.W, pady=(6, 0))

        self._refresh_color()
        self._refresh_fixed()
        self.set_tool("pan")

    def _on_space_down(self, event):
        self._space_down = True

    def _on_space_up(self, event):
        self._space_down = False

    def set_tool(self, key):
        self.tool = key
        for k, btn in self.tool_buttons.items():
            btn.configure(style="Primary.TButton" if k == key else "Tool.TButton")
        if self.preview_img:
            self.redraw_preview()

    def set_color(self, rgb, tool=None):
        self.current_color = tuple(int(v) for v in rgb)[:3]
        if tool:
            self.set_tool(tool)
        self._refresh_color()

    def _refresh_color(self):
        r, g, b = self.current_color
        hexc = _rgb_to_hex(self.current_color)
        size = self.SWATCH_BIG
        self.swatch.config(bg=hexc)
        self.swatch.delete("all")
        # 高亮边框占掉四周 1px，只画内部，否则右边/下边会露白线
        self.swatch.create_rectangle(
            1, 1, size - 2, size - 2, fill=hexc, outline=""
        )
        self.color_label.config(text=hexc)

    def _refresh_fixed(self):
        cv = self.fix_canvas
        cv.delete("all")
        self._fixed = list(FIXED_COLORS) + [None]
        size, gap = self.SWATCH, self.SWATCH_GAP
        for n, hexc in enumerate(self._fixed):
            row, col = divmod(n, self.FIXED_COLS)
            x = col * (size + gap)
            y = row * (size + gap)
            if hexc is None:
                self._draw_hatch(cv, x, y, size, size)
            else:
                cv.create_rectangle(x, y, x + size, y + size, fill=hexc,
                                    outline=self.c["border_active"])

    def _draw_hatch(self, cv, x, y, w, h):
        """透明格：棋盘格，和画布上「已抠除」的表示一致。"""
        cv.create_rectangle(x, y, x + w, y + h, fill="#EDEDED",
                            outline=self.c["border_active"])
        step = 7
        for ry in range(int(h // step) + 1):
            for rx in range(int(w // step) + 1):
                if (rx + ry) % 2:
                    continue
                sx, sy = x + rx * step, y + ry * step
                cv.create_rectangle(sx, sy, min(sx + step, x + w),
                                    min(sy + step, y + h), fill="#B4B4B4",
                                    outline="")

    def _on_fixed_click(self, event):
        size = self.SWATCH + self.SWATCH_GAP
        col = int(event.x // size)
        row = int(event.y // size)
        n = row * self.FIXED_COLS + col
        if not (0 <= n < len(self._fixed)):
            return
        color = self._fixed[n]
        if color is None:
            self.set_tool("erase")
            return
        self.set_color(_hex_to_rgb(color))

    def _on_palette_click(self, event):
        for x0, y0, x1, y1, rgb in self._swatches:
            if x0 <= event.x < x1 and y0 <= event.y < y1:
                self.set_color(rgb)
                return

    def _refresh_palette(self):
        cv = self.pal_canvas
        cv.delete("all")
        self._swatches = []
        if self.mosaic_img is None:
            return
        colors = extract_palette(self.mosaic_img, count=PALETTE_SIZE)
        size, gap = self.SWATCH, self.SWATCH + self.SWATCH_GAP
        for n, rgb in enumerate(colors):
            row, col = divmod(n, self.SWATCH_COLS)
            x = col * gap
            y = row * gap
            cv.create_rectangle(x, y, x + size, y + size, fill=_rgb_to_hex(rgb),
                                outline=self.c["border_active"])
            self._swatches.append((x, y, x + size, y + size, rgb))

    # ---------- 画布编辑 ----------

    def _cell_at(self, x, y):
        """画布坐标 → 马赛克块坐标；不在图上返回 None。"""
        if self.mosaic_img is None or self._draw_pos is None:
            return None
        tw, th = self._draw_size
        left = self._draw_pos[0] - tw / 2
        top = self._draw_pos[1] - th / 2
        gw, gh = self.current_grid
        i = int((x - left) / tw * gw)
        j = int((y - top) / th * gh)
        if 0 <= i < gw and 0 <= j < gh:
            return i, j
        return None

    def _panning(self):
        return self.tool == "pan" or self._space_down

    def on_canvas_press(self, event):
        if self._panning() or self.mosaic_img is None:
            self.on_pan_start(event)
            return
        cell = self._cell_at(event.x, event.y)
        if cell is None:
            self.on_pan_start(event)
            return
        if self.tool == "pick":
            self._pick_cell(cell)
            return
        item = self.current
        item.begin_edit()
        self._stroke_cells = set()
        self._paint_cell(cell)

    def on_canvas_motion(self, event):
        if self.pan_start is not None:
            self.on_pan_move(event)
            return
        if self._stroke_cells:
            cell = self._cell_at(event.x, event.y)
            if cell is not None:
                self._paint_cell(cell)

    def on_canvas_release(self, event):
        if self._stroke_cells:
            self._stroke_cells = set()
            self._update_edit_state()
        self.pan_start = None
        self.anchor_start = None

    def on_middle_press(self, event):
        """中键拖拽 = 任何工具下都能平移。"""
        self.on_pan_start(event)

    def on_middle_motion(self, event):
        self.on_pan_move(event)

    def on_middle_release(self, event):
        self.pan_start = None
        self.anchor_start = None

    def _pick_cell(self, cell):
        """吸管：取该格当前显示的颜色（编辑过的也算数，所见即所得）。"""
        item = self.current
        i, j = cell
        x0, y0, x1, y1 = cell_rect(
            item.img.size[0], item.img.size[1], self.current_grid, i, j
        )
        box = self.preview_img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)))
        colors = box.convert("RGB").getcolors(x1 * y1 + 1) or []
        colors.sort(key=lambda pair: -pair[0])
        if colors:
            self._refresh_color()
            self.set_color(colors[0][1])

    def _paint_cell(self, cell):
        if cell in self._stroke_cells:
            return
        self._stroke_cells.add(cell)
        item = self.current
        i, j = cell
        rect = cell_rect(item.img.size[0], item.img.size[1], self.current_grid, i, j)
        color = None if self.tool == "erase" else self.current_color
        item.patches.append(EditPatch(*rect, color))
        if self.preview_img is not None:
            self.preview_img = apply_patches(self.preview_img, [item.patches[-1]])
            self._rev += 1
        self.redraw_preview()

    def _focused_entry(self):
        try:
            focus = self.root.focus_get()
        except Exception:
            return False
        return isinstance(focus, (tk.Entry, ttk.Entry))

    def undo_edit(self):
        if self._focused_entry():
            return "break"
        item = self.current
        if item is None or not item.undo_edit():
            return "break"
        self.preview_mosaic()
        self._update_edit_state()
        return "break"

    def redo_edit(self):
        if self._focused_entry():
            return "break"
        item = self.current
        if item is None or not item.redo_edit():
            return "break"
        self.preview_mosaic()
        self._update_edit_state()
        return "break"

    def reset_edits(self):
        item = self.current
        if item is None or not item.patches:
            return
        item.begin_edit()
        item.clear_edits()
        self.preview_mosaic()
        self._update_edit_state()

    def _update_edit_state(self):
        item = self.current
        n = len(item.patches) if item else 0
        self.reset_edits_btn.state(["!disabled"] if n else ["disabled"])
        if n:
            self.set_status(
                f"已加载（第 {self.index + 1}/{len(self.queue)} 张）| 已编辑 {n} 处"
                f"（Ctrl+Z 撤销）"
            )

    @property
    def current(self):
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    def _apply_list_colors(self):
        self.list_box.config(
            bg=self.c["surface"],
            fg=self.c["ink"],
            selectbackground=self.c["accent"],
            selectforeground=self.c["on_accent"],
            highlightbackground=self.c["border"],
        )

    def _sync_scrollbar(self):
        if len(self.queue) > self.LIST_ROWS:
            if not self.list_scroll.winfo_manager():
                self.list_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(3, 0))
        elif self.list_scroll.winfo_manager():
            self.list_scroll.pack_forget()

    def _refresh_list(self):
        self.list_box.delete(0, tk.END)
        for item in self.queue:
            self.list_box.insert(tk.END, item.stem)
        if self.current is not None:
            self.list_box.selection_clear(0, tk.END)
            self.list_box.selection_set(self.index)
            self.list_box.see(self.index)
        self.queue_count.set(f"待处理（{len(self.queue)} 张）")
        self._sync_scrollbar()
        self._update_states()

    def _update_states(self):
        has = self.current is not None
        many = len(self.queue) > 1
        self.save_btn.state(["!disabled"] if has else ["disabled"])
        for btn in (self.remove_btn, self.clear_btn, self.name_reset_btn):
            btn.state(["!disabled"] if has else ["disabled"])
        self.apply_all_btn.state(["!disabled"] if many else ["disabled"])
        self.save_btn.config(
            text=f"保存全部（{len(self.queue)} 张）" if many else "保存图片"
        )

    def item_name(self, item=None, index=None, total=None):
        item = item or self.current
        if item is None:
            return ""
        total = len(self.queue) if total is None else total
        if index is None:
            index = self.queue.index(item) + 1
        return item.rendered(index, total, self.current_grid)

    def current_name(self):
        return self.item_name(self.current)

    def _set_name_var(self, text):
        self._syncing_name = True
        self.name_var.set(text)
        self._syncing_name = False

    def _on_name_edited(self, *_):
        if self._syncing_name:
            return
        item = self.current
        if item is not None:
            item.tpl = self.name_var.get()
        self._update_name_preview()

    def reset_current_name(self):
        item = self.current
        if item is None:
            return
        item.tpl = DEFAULT_NAME_TEMPLATE
        self._set_name_var(item.tpl)
        self._update_name_preview()

    def apply_name_to_all(self):
        item = self.current
        if item is None or len(self.queue) < 2:
            return
        for other in self.queue:
            other.tpl = item.tpl
        self._update_name_preview()

    def _update_name_preview(self):
        total = len(self.queue)
        self.name_hint_var.set(
            NAME_HINT if total < 2 else NAME_HINT_MANY
        )
        item = self.current
        if item is None:
            self.name_preview.config(text="")
            return
        if self.name_var.get() != item.tpl:
            self._set_name_var(item.tpl)
        self.name_preview.config(text=f"→ {self.item_name(item)}.png")

    def toggle_theme(self):
        self.set_theme("light" if self.dark else "dark")

    def set_theme(self, name, save=True):
        self.dark = name == "dark"
        self.c = DARK if self.dark else LIGHT
        build_theme(self.root, self.c)
        self.canvas.config(bg=self.c["canvas"])
        self.sep.config(bg=self.c["border"])
        self.theme_sep.config(bg=self.c["border"])
        self._apply_list_colors()
        self.swatch.config(highlightbackground=self.c["border_active"])
        self.pal_canvas.config(bg=self.c["surface"])
        self.fix_canvas.config(bg=self.c["surface"])
        self._refresh_palette()
        self._refresh_fixed()
        self._refresh_color()
        self.set_tool(self.tool)
        self.theme_switch.apply_palette(self.c)
        if self.theme_switch.on != self.dark:
            self.theme_switch.set_on(self.dark)
        enable_dark_titlebar(self.root, self.dark)
        self.redraw_preview()
        self.root.after_idle(self._style_combobox_popup)
        if save:
            save_theme_pref(name)

    def _style_combobox_popup(self):
        try:
            pop = self.grid_box.tk.call(
                "ttk::combobox::PopdownWindow", self.grid_box._w
            )
            self.grid_box.tk.call(
                f"{pop}.f.l",
                "configure",
                "-background",
                self.c["bg"],
                "-foreground",
                self.c["ink"],
                "-selectbackground",
                self.c["accent"],
                "-selectforeground",
                self.c["on_accent"],
                "-highlightthickness",
                "0",
            )
        except Exception:
            pass

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        imgs = [f for f in files if f.lower().endswith(IMAGE_EXTS)]
        if imgs:
            self.add_images(imgs)
        else:
            messagebox.showwarning("提示", "拖入的文件不是支持的图片格式")

    def pick_image(self):
        paths = filedialog.askopenfilenames(
            title="添加图片（可多选）",
            filetypes=[
                ("图片文件", " ".join(f"*{e}" for e in IMAGE_EXTS)),
                ("所有文件", "*.*"),
            ],
        )
        if paths:
            self.add_images(list(paths))

    def add_images(self, paths):
        """追加到队列末尾；原来加载着的图不会被顶掉。"""
        items = []
        errors = []
        for p in paths:
            try:
                img = Image.open(p)
                img = ImageOps.exif_transpose(img)
                if has_alpha(img):
                    img = img.convert("RGBA")   # 保留原有透明区，别转成 RGB 把它烤成黑块
                else:
                    img = img.convert("RGB")
                items.append(QueueItem(p, img, DEFAULT_NAME_TEMPLATE))
            except Exception as e:
                errors.append(f"{os.path.basename(p)}: {e}")
        if not items:
            messagebox.showerror("错误", f"无法打开图片:\n{errors[0]}")
            return
        if errors:
            messagebox.showwarning(
                "提示", "部分文件无法打开，已跳过:\n" + "\n".join(errors[:5])
            )
        was_empty = not self.queue
        self.queue.extend(items)
        # 新导入的图默认按原分辨率看（网格数 = 像素尺寸），切图时不重置
        self.grid_mode = GRID_NATIVE
        if was_empty:
            self.show_index(0)
        else:
            self._refresh_list()
            self._update_name_preview()
            self.preview_mosaic()
            self.set_status(
                f"已添加 {len(items)} 张，当前队列 {len(self.queue)} 张"
            )

    def clear_queue(self):
        if not self.queue:
            return
        self.queue.clear()
        self.index = -1
        self._reset_preview()
        self._set_name_var(DEFAULT_NAME_TEMPLATE)
        self._refresh_list()
        self._refresh_palette()
        self._update_name_preview()
        self._update_edit_state()
        self.set_status("已清空队列")
        self.redraw_preview()

    def remove_current(self):
        item = self.current
        if item is None:
            return
        idx = self.index
        self.queue.pop(idx)
        self._reset_preview()
        if not self.queue:
            self.index = -1
            self._set_name_var(DEFAULT_NAME_TEMPLATE)
            self.set_status(f"已删除: {os.path.basename(item.path)}")
            self._refresh_list()
            self._refresh_palette()
            self._update_name_preview()
            self._update_edit_state()
            self.redraw_preview()
            return
        self.index = min(idx, len(self.queue) - 1)
        self._refresh_list()
        self.show_index(self.index)

    def _reset_preview(self):
        self.preview_img = None
        self.mosaic_img = None
        self.zoom = 1.0
        self.anchor = None

    def _on_list_select(self, event):
        sel = self.list_box.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx != self.index:
            self.show_index(idx)

    def _on_list_wheel(self, event):
        self.list_box.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def step(self, delta):
        if len(self.queue) < 2:
            return
        self.show_index((self.index + delta) % len(self.queue))

    def show_index(self, idx):
        if not (0 <= idx < len(self.queue)):
            return
        self.index = idx
        item = self.queue[idx]
        self._reset_preview()
        self._refresh_list()
        self._update_name_preview()
        self.preview_mosaic()
        self._update_edit_state()

    def _grid_values(self):
        item = self.current
        native = grid_label(GRID_NATIVE, item.img.size) if item else "原分辨率"
        return [native] + [f"{g}x{g}" for g in MOSAIC_GRIDS]

    def _sync_grid_box(self):
        """下拉里第一项是随图变化的「原分辨率」，其余是固定方形档。"""
        self.grid_box.config(values=self._grid_values())
        idx = 0 if self.grid_mode == GRID_NATIVE else (
            MOSAIC_GRIDS.index(self.grid_mode) + 1
            if self.grid_mode in MOSAIC_GRIDS
            else 0
        )
        self.grid_box.current(idx)

    def on_grid_pick(self, event=None):
        idx = max(self.grid_box.current(), 0)
        self.grid_mode = GRID_NATIVE if idx == 0 else MOSAIC_GRIDS[idx - 1]
        self.preview_mosaic()

    def set_grid_mode(self, mode):
        self.grid_mode = mode
        self._sync_grid_box()
        self.preview_mosaic()

    def preview_mosaic(self):
        item = self.current
        if item is None:
            return
        grid = grid_dims(self.grid_mode, item.img.size)
        self.current_grid = grid
        self._sync_grid_box()
        self.mosaic_img = apply_mosaic(item.img, grid)
        self.preview_img = apply_patches(self.mosaic_img, item.patches)
        self._rev += 1
        total = len(self.queue)
        pos = f"（第 {self.index + 1}/{total} 张）" if total > 1 else ""
        label = grid_label(self.grid_mode, item.img.size)
        self.set_status(
            f"已加载{pos}: {os.path.basename(item.path)} "
            f"({item.img.size[0]}x{item.img.size[1]}) | 预览倍率 {label}"
        )
        self._refresh_palette()
        self._update_name_preview()
        self.redraw_preview()

    def _draw_erased(self, ax, ay, tw, th):
        """被抠掉的块画成浅色棋盘格（导出为真透明）。"""
        item = self.current
        if item is None or not item.patches:
            return
        w, h = item.img.size
        left, top = ax - tw / 2, ay - th / 2
        holes = [p for p in item.patches if p.color is None]
        if not holes:
            return
        budget = ERASED_PATTERN_BUDGET
        for p in holes:
            x0 = left + p.x0 / w * tw
            y0 = top + p.y0 / h * th
            x1 = left + p.x1 / w * tw
            y1 = top + p.y1 / h * th
            self.canvas.create_rectangle(
                x0, y0, x1, y1, fill="#EDEDED", outline=self.c["border_active"]
            )
            if budget <= 0:
                continue
            # 方块数按面积分摊到预算内，块太大就退化成纯色
            step = max(7, int(((x1 - x0) * (y1 - y0) / budget) ** 0.5) + 1)
            rows = int((y1 - y0) // step) + 1
            cols = int((x1 - x0) // step) + 1
            for ry in range(rows):
                for rx in range(cols):
                    if (rx + ry) % 2:
                        continue
                    sx = x0 + rx * step
                    sy = y0 + ry * step
                    self.canvas.create_rectangle(
                        sx, sy, min(sx + step, x1), min(sy + step, y1),
                        fill="#B4B4B4", outline="",
                    )
            budget -= max(rows * cols // 2, 1)

    def _hint_text(self, z):
        tips = {
            "pan": "左键拖动平移",
            "pick": "左键点格子取色",
            "paint": "左键涂格子（可拖动），空格拖动平移",
            "erase": "左键抠掉格子（可拖动），空格拖动平移",
        }
        return f"{z * 100:.0f}%  |  {tips.get(self.tool, '')}  |  滚轮缩放，双击复原"

    def _checker_bg(self, tw, th):
        """7px 棋盘格底：在目标分辨率上按行拼出来。

        别想着「画个小 tile 再放大」——NEAREST 会把格子一起放大成大色块（踩过）。
        """
        k = ERASED_CHECKER_PX
        w = max(tw // k * k, 2 * k)
        h = max(th // k * k, 2 * k)
        strips = []
        for offset in (0, k):
            strip = Image.new("RGB", (w, k), "#EDEDED")
            d = ImageDraw.Draw(strip)
            for x in range(offset, w, 2 * k):
                d.rectangle([x, 0, x + k - 1, k - 1], fill="#B4B4B4")
            strips.append(strip)
        bg = Image.new("RGB", (w, h), "#EDEDED")
        for row in range(h // k):
            bg.paste(strips[row % 2], (0, row * k))
        return bg.crop((0, 0, tw, th))

    def _preview_rgb(self, tw, th):
        """缩到 (tw, th) 并把透明区域画成棋盘格（所见即所得：棋盘格 = 导出后的透明）。"""
        img = self.preview_img.resize((tw, th), Image.Resampling.NEAREST)
        if img.mode != "RGBA":
            return img
        alpha = img.getchannel("A")
        if alpha.getextrema()[0] == 255:
            return img.convert("RGB")
        return Image.composite(img.convert("RGB"), self._checker_bg(tw, th), alpha)

    def _fit_buffer(self, tw, th):
        """限制绘制缓冲大小：Tk 的 PhotoImage 是逐像素拷贝，放大到上万像素会爆内存。"""
        if tw * th <= MAX_PREVIEW_PIXELS:
            return tw, th
        k = (MAX_PREVIEW_PIXELS / (tw * th)) ** 0.5
        return max(int(tw * k), 1), max(int(th * k), 1)

    def _photo_for(self, tw, th):
        key = (tw, th, self._rev)
        if self._photo_cache and self._photo_cache[0] == key:
            return self._photo_cache[1]
        photo = ImageTk.PhotoImage(self._preview_rgb(tw, th))
        self._photo_cache = (key, photo)
        return photo

    def redraw_preview(self):
        if not self.preview_img:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                text="拖入或选择图片开始",
                fill=self.c["canvas_text"],
                font=("Microsoft YaHei UI", 12),
            )
            return
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        w, h = self.preview_img.size
        base = min(min(cw / w, ch / h), 1.0)
        self.base_scale = base
        z = self.zoom
        tw, th = max(int(w * base * z), 1), max(int(h * base * z), 1)
        tw, th = self._fit_buffer(tw, th)
        self._draw_size = (tw, th)
        self.preview_scale = base * z
        if self.anchor is None:
            ax, ay = cw / 2, ch / 2
        else:
            ax, ay = self.anchor
        self._draw_pos = (ax, ay)
        photo = self._photo_for(tw, th)
        self.canvas.delete("all")
        self.canvas.create_image(ax, ay, image=photo, anchor=tk.CENTER)
        if self.grid_lines.get():
            gw, gh = self.current_grid
            step_x, step_y = tw / gw, th / gh
            line_color = self.c["grid_line"]
            # 格太密就别画了：几千条线每次重绘都要重建，纯属自己找罪受
            if step_x >= 3 and step_y >= 3 and gw + gh <= GRID_LINE_LIMIT:
                x0, y0 = ax - tw / 2, ay - th / 2
                for i in range(1, gw):
                    x = x0 + i * step_x
                    self.canvas.create_line(
                        x, y0, x, y0 + th, fill=line_color, stipple="gray50"
                    )
                for j in range(1, gh):
                    y = y0 + j * step_y
                    self.canvas.create_line(
                        x0, y, x0 + tw, y, fill=line_color, stipple="gray50"
                    )
        self._draw_erased(ax, ay, tw, th)
        self.canvas.create_text(
            10, 8, anchor=tk.NW, fill=self.c["canvas_hint"],
            font=("Microsoft YaHei UI", 9), text=self._hint_text(z),
        )
        self.canvas.image = photo

    def on_wheel(self, event):
        if self.preview_img is None:
            return
        factor = 1.2 if event.delta > 0 else 1 / 1.2
        new_zoom = min(max(self.zoom * factor, 0.05), 24)
        if abs(new_zoom - self.zoom) < 1e-9:
            return
        w, h = self.preview_img.size
        tw = max(w * self.base_scale * self.zoom, 1)
        th = max(h * self.base_scale * self.zoom, 1)
        ax0, ay0 = self.anchor if self.anchor else (
            max(self.canvas.winfo_width(), 10) / 2,
            max(self.canvas.winfo_height(), 10) / 2,
        )
        rel_x = (event.x - ax0) / tw + 0.5
        rel_y = (event.y - ay0) / th + 0.5
        tw2 = max(w * self.base_scale * new_zoom, 1)
        th2 = max(h * self.base_scale * new_zoom, 1)
        self.anchor = (event.x + tw2 * (0.5 - rel_x), event.y + th2 * (0.5 - rel_y))
        self.zoom = new_zoom
        self.redraw_preview()

    def on_pan_start(self, event):
        if self.preview_img is None:
            return
        if self.anchor is None:
            self.anchor = (
                max(self.canvas.winfo_width(), 10) / 2,
                max(self.canvas.winfo_height(), 10) / 2,
            )
        self.pan_start = (event.x, event.y)
        self.anchor_start = self.anchor

    def on_pan_move(self, event):
        if self.preview_img is None or self.pan_start is None:
            return
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        self.anchor = (self.anchor_start[0] + dx, self.anchor_start[1] + dy)
        self.redraw_preview()

    def reset_zoom(self):
        self.zoom = 1.0
        self.anchor = None
        self.redraw_preview()

    def browse_save_dir(self):
        d = filedialog.askdirectory(title="选择保存目录", initialdir=self.save_dir)
        if d:
            self.save_dir = d
            self.path_var.set(d)

    # ---------- 保存进度浮层 ----------

    def _build_overlay(self, parent):
        self.overlay = ttk.Frame(parent, style="Panel.TFrame", padding=(12, 8))
        self.overlay_bar = ttk.Progressbar(
            self.overlay, mode="determinate", maximum=100, length=240,
            style="Save.TProgressbar",
        )
        self.overlay_bar.pack(fill=tk.X, pady=(0, 4))
        self.overlay_label = ttk.Label(
            self.overlay, text="", style="Panel.Muted.TLabel", anchor=tk.W
        )
        self.overlay_label.pack(fill=tk.X)
        self.overlay.place_forget()

    def _show_overlay(self, text, pct=None, done=False):
        if pct is None:
            self.overlay_bar.pack_forget()
        else:
            self.overlay_bar.pack(fill=tk.X, pady=(0, 4), before=self.overlay_label)
            self.overlay_bar.config(value=pct)
        self.overlay_label.config(
            text=text,
            style="Primary.TLabel" if done else "Panel.Muted.TLabel",
        )
        self.overlay.place(relx=0.5, rely=1.0, anchor="s", y=-14)
        self.root.update_idletasks()

    def _hide_overlay(self):
        self.overlay.place_forget()

    def _flash_saved(self, text, ms=1800):
        self._show_overlay(text, done=True)
        self.root.after(ms, self._hide_overlay)

    def _target_dir(self):
        """侧栏「保存路径」就是落盘位置：不存在就建，不是文件夹就报错。"""
        d = (self.path_var.get() or "").strip() or exe_dir()
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法使用保存路径:\n{d}\n{e}")
            return None
        if not os.path.isdir(d):
            messagebox.showerror("错误", f"保存路径不是文件夹:\n{d}")
            return None
        self.save_dir = d
        return d

    def save_image(self):
        if self.current is None or self.preview_img is None:
            return
        if self.save_btn.instate(["disabled"]):
            return
        d = self._target_dir()
        if d is None:
            return
        self.save_btn.state(["disabled"])
        try:
            if len(self.queue) > 1:
                self._save_all(d)
                return
            name = f"{self.current_name()}.png"
            self._show_overlay(f"正在保存 {name} …")
            out = unique_path(os.path.join(d, name))
            self.preview_img.save(out)
        except Exception as e:
            self._hide_overlay()
            messagebox.showerror("错误", f"保存失败:\n{e}")
            return
        finally:
            self.save_btn.state(["!disabled"])
        self.set_status(f"已保存: {out}")
        self._flash_saved(f"✓ 已保存 {name} → {_short_path(d)}")

    def _save_all(self, d):
        total = len(self.queue)
        self._show_overlay(f"正在保存 0/{total} …", 0)
        for n, item in enumerate(self.queue, 1):
            name = f"{item.rendered(n, total, self.current_grid)}.png"
            out = unique_path(os.path.join(d, name))
            try:
                render_mosaic(item.img, self.current_grid, item.patches).save(out)
            except Exception as e:
                self._hide_overlay()
                messagebox.showerror("错误", f"保存失败:\n{e}")
                return
            self._show_overlay(f"正在保存 {n}/{total} · {name}", n / total * 100)
        self.set_status(
            f"已保存 {total} 张到 {d} | 倍率 "
            f"{grid_label(self.grid_mode, self.current.img.size)}"
        )
        self._flash_saved(f"✓ 已保存 {total} 张 → {_short_path(d)}", 2400)

    def set_status(self, text):
        self.status.config(text=text)


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def icon_candidates():
    paths = [os.path.join(exe_dir(), ICON_NAME)]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        paths.append(os.path.join(meipass, ICON_NAME))
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ICON_NAME))
    return [p for p in paths if os.path.exists(p)]


def apply_window_icon(root):
    """把 icon.ico 设成窗口/任务栏图标。

    Tk 的 `wm iconbitmap` 在 Windows 上是静默空操作，只能走 Win32：
    LoadImageW 从文件取 HICON（restype 必须设成 64 位指针，否则句柄被截断成 32 位），
    再 WM_SETICON 打到 GetAncestor(GA_ROOT) 那个真正的顶层窗口上。
    """
    try:
        candidates = icon_candidates()
        if not candidates:
            return
        ico = candidates[0]
        user32 = ctypes.windll.user32
        user32.SendMessageW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_size_t,
        ]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        load = user32.LoadImageW
        load.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        load.restype = ctypes.c_void_p
        hwnd = user32.GetAncestor(root.winfo_id(), 2)
        if not hwnd:
            return
        LR_LOADFROMFILE = 0x00000010
        IMAGE_ICON = 1
        WM_SETICON = 0x0080
        for icon_type, size in ((1, 32), (0, 16)):
            hicon = load(None, ico, IMAGE_ICON, size, size, LR_LOADFROMFILE)
            if hicon:
                user32.SendMessageW(hwnd, WM_SETICON, icon_type, hicon)
    except Exception:
        pass


def enable_dark_titlebar(root, dark=True):
    try:
        hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2)
        value = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):
            if (
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                )
                == 0
            ):
                break
    except Exception:
        pass


def main():
    enable_dpi_awareness()
    root = TkinterDnD.Tk()
    app = MosaicApp(root)
    root.update_idletasks()
    enable_dark_titlebar(root, app.dark)
    apply_window_icon(root)
    # Tk 在 deiconify / 重新映射时会把图标打回默认 feathers，故每次 Map 都补一次
    root.bind("<Map>", lambda e: root.after(60, apply_window_icon, root))
    if "--smoke-test" in sys.argv:
        root.after(400, lambda: app.set_theme("dark", save=False))
        root.after(800, lambda: app.set_theme("light", save=False))
        root.after(1200, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
