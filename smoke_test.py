import sys

from PIL import Image

from mosaic_app import apply_mosaic

img = Image.new("RGB", (300, 200), (255, 0, 0))
out = apply_mosaic(img, 24)
assert out.size == (300, 200), out.size
assert out.getpixel((0, 0)) == (255, 0, 0)

img2 = Image.new("RGB", (97, 53), (0, 255, 0))
out2 = apply_mosaic(img2, 64)
assert out2.size == (97, 53)
assert out2.getpixel((10, 10)) == (0, 255, 0)

img3 = Image.new("RGB", (400, 400), (0, 0, 255))
out3 = apply_mosaic(img3, 128)
assert out3.size == (400, 400)
print("algorithm OK")

from mosaic_app import MOSAIC_GRIDS
assert MOSAIC_GRIDS == [16, 24, 32, 48, 64, 96, 128]
assert 128 == max(MOSAIC_GRIDS)
print("grids OK")

from mosaic_app import DARK, LIGHT

assert set(LIGHT) == set(DARK), set(LIGHT) ^ set(DARK)
assert LIGHT["bg"] != DARK["bg"]
assert LIGHT["ink"] != DARK["ink"]
assert LIGHT["accent"] == DARK["accent"] == "#FFC700"
assert LIGHT["on_accent"] == DARK["on_accent"] == "#1A1A1A"
assert DARK["canvas"] != LIGHT["canvas"]


def _lum(hex_color):
    out = []
    for i in (1, 3, 5):
        ch = int(hex_color[i : i + 2], 16) / 255
        out.append(
            ch / 12.92
            if ch <= 0.04045
            else ((ch + 0.055) / 1.055) ** 2.4
        )
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(fg, bg):
    a, b = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


for name, c in (("light", LIGHT), ("dark", DARK)):
    assert _ratio(c["ink"], c["bg"]) >= 4.5, (name, _ratio(c["ink"], c["bg"]))
    assert _ratio(c["muted"], c["bg"]) >= 4.5, (name, _ratio(c["muted"], c["bg"]))
    assert _ratio(c["on_accent"], c["accent"]) >= 4.5, (name, "on_accent")
    assert _ratio(c["ink"], c["surface"]) >= 4.5, (name, _ratio(c["ink"], c["surface"]))
print("palettes OK")

from mosaic_app import DEFAULT_NAME_TEMPLATE, render_name_template

assert render_name_template("", "cat", 1, 1, 64) == "cat_马赛克_64x64"
assert render_name_template(DEFAULT_NAME_TEMPLATE, "猫", 3, 7, 32) == "猫_马赛克_32x32"
assert render_name_template("{原名}_{序号}_{总数}", "a b", 2, 5, 16) == "a b_02_05"
assert render_name_template("   ", "fallback", 1, 1, 16) == "fallback_马赛克_16x16"
assert render_name_template("{原名}", "x/y:z*?", 1, 1, 16) == "x_y_z__"
assert render_name_template("...", "keep", 1, 1, 16) == "keep"
assert render_name_template("{倍率}", "z", 1, 1, 128) == "128x128"
print("name template OK")

from mosaic_app import QueueItem

item = QueueItem(r"D:\ pics\猫.png", None, "{原名}_{序号}")
assert item.stem == "猫"
assert item.rendered(2, 5, 32) == "猫_02"
assert item.rendered(1, 5, 128) == "猫_01"
print("queue item OK")

from mosaic_app import EditPatch, apply_patches, cell_rect, extract_palette, render_mosaic

base = Image.new("RGB", (10, 10), (1, 2, 3))
assert apply_patches(base, []).getpixel((0, 0)) == (1, 2, 3, 255)
assert apply_patches(base, []).mode == "RGBA"

out = apply_patches(base, [EditPatch(0, 0, 5, 5, (9, 9, 9))])
assert out.getpixel((0, 0)) == (9, 9, 9, 255)
assert out.getpixel((4, 4)) == (9, 9, 9, 255)
assert out.getpixel((5, 5)) == (1, 2, 3, 255)

out = apply_patches(base, [EditPatch(2, 2, 4, 4, None)])
assert out.getpixel((3, 3))[3] == 0
assert out.getpixel((0, 0))[3] == 255

out = apply_patches(base, [EditPatch(-5, -5, 3, 3, (7, 7, 7))])
assert out.getpixel((0, 0)) == (7, 7, 7, 255)
assert out.getpixel((5, 5)) == (1, 2, 3, 255)
out = apply_patches(base, [EditPatch(8, 8, 99, 99, (7, 7, 7))])
assert out.getpixel((9, 9)) == (7, 7, 7, 255)

out = apply_patches(base, [EditPatch(0, 0, 2, 2, (1, 1, 1)),
                           EditPatch(1, 1, 3, 3, (2, 2, 2))])
assert out.getpixel((1, 1)) == (2, 2, 2, 255), "后贴的应盖住先贴的"
assert out.getpixel((0, 0)) == (1, 1, 1, 255)

assert cell_rect(100, 50, 4, 0, 0) == (0, 0, 25, 12)
assert cell_rect(100, 50, 4, 3, 1) == (75, 12, 100, 25)
assert cell_rect(10, 10, 128, 0, 0) == (0, 0, 1, 1), "格子比像素还密时不能出空块"
assert cell_rect(100, 50, (4, 4), 0, 0) == (0, 0, 25, 12), "方形档用元组也要一致"
assert cell_rect(100, 50, (10, 5), 1, 1) == (10, 10, 20, 20)
assert cell_rect(900, 640, (900, 640), 5, 7) == (5, 7, 6, 8), "原分辨率=每像素一格"

swatch = Image.new("RGB", (40, 40), (0, 0, 0))
for y in range(40):
    for x in range(30):
        swatch.putpixel((x, y), (255, 0, 0))
pal = extract_palette(swatch, count=3, min_distance=10)
assert pal[0] == (255, 0, 0), pal
assert (0, 0, 0) in pal, pal
assert len(extract_palette(swatch, count=1)) == 1
assert extract_palette(Image.new("RGB", (8, 8), (10, 20, 30)), count=4) == [(10, 20, 30)]

rendered = render_mosaic(Image.new("RGB", (40, 40), (0, 0, 0)), 4,
                         [EditPatch(0, 0, 10, 10, (1, 2, 3))])
assert rendered.size == (40, 40) and rendered.mode == "RGBA"
assert rendered.getpixel((5, 5)) == (1, 2, 3, 255)
assert rendered.getpixel((30, 30)) == (0, 0, 0, 255)

# 原分辨率档：网格 = 像素尺寸 -> 输出与原图逐像素一致
from mosaic_app import GRID_NATIVE, grid_dims, grid_label

src = Image.new("RGB", (5, 3))
sp = src.load()
for x in range(5):
    for y in range(3):
        sp[x, y] = (x * 40, y * 80, 7)
assert grid_dims(GRID_NATIVE, src.size) == (5, 3)
assert grid_dims(64, src.size) == (64, 64)
assert grid_label(GRID_NATIVE, src.size) == "原分辨率 5x3"
assert grid_label(32, src.size) == "32x32"
native = apply_mosaic(src, grid_dims(GRID_NATIVE, src.size))
assert native.size == src.size
assert native.tobytes() == src.tobytes(), "原分辨率不该改变任何像素"
assert render_mosaic(src, (5, 3)).getpixel((3, 2)) == (120, 160, 7, 255)
assert render_name_template("{倍率}", "z", 1, 1, (5, 3)) == "5x3"
assert apply_mosaic(src, (2, 3)).size == src.size
print("native grid OK")

# 透明区必须保留，不能被烤成黑块
from mosaic_app import MAX_PREVIEW_PIXELS, has_alpha, MosaicApp

rgba = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
rgba.putpixel((3, 3), (200, 0, 0, 0))
assert has_alpha(rgba)
assert not has_alpha(Image.new("RGB", (4, 4)))
pal_img = Image.new("P", (4, 4))
pal_img.info["transparency"] = 0
assert has_alpha(pal_img), "调色板 PNG 的 transparency 也要认"
assert not has_alpha(Image.new("L", (4, 4)))

kept = Image.alpha_composite(Image.new("RGBA", (8, 8), (0, 0, 0, 0)), rgba)
assert kept.getpixel((3, 3))[3] == 0, "透明像素仍是透明"
assert kept.getpixel((0, 0))[3] == 255
baked = rgba.convert("RGB").getpixel((3, 3))
assert baked == (200, 0, 0), "这正是要避免的『透明被烤成实色』"

# 透明区的颜色不能污染调色盘（叠白底后应接近白）
clear = Image.new("RGBA", (40, 40), (10, 200, 10, 255))
clear.paste((0, 0, 0, 0), (0, 0, 40, 20))
pal = extract_palette(clear, count=4, min_distance=10)
assert (10, 200, 10) in pal, pal
assert not any(c == (0, 0, 0) for c in pal), f"透明区被当成黑色：{pal}"

# 绘制缓冲上限：再大的缩放也不能超过 MAX_PREVIEW_PIXELS
app = MosaicApp.__new__(MosaicApp)
assert MosaicApp._fit_buffer(app, 40000, 40000)[0] * \
    MosaicApp._fit_buffer(app, 40000, 40000)[1] <= MAX_PREVIEW_PIXELS
assert MosaicApp._fit_buffer(app, 700, 500) == (700, 500), "正常尺寸不裁剪"
assert MosaicApp._fit_buffer(app, 100, 100) == (100, 100)
print("alpha & buffer OK")
print("edits OK")

from mosaic_app import QueueItem as _QI

item = _QI("a.png", None, "{原名}")
p1, p2 = EditPatch(0, 0, 1, 1, (1, 1, 1)), EditPatch(1, 1, 2, 2, (2, 2, 2))
item.begin_edit()
item.patches.append(p1)
item.begin_edit()
item.patches.append(p2)
assert len(item.patches) == 2 and len(item.undo) == 2
assert item.undo_edit() and item.patches == [p1]
assert item.redo_edit() and item.patches == [p1, p2]
assert item.undo_edit() and item.undo_edit() and item.patches == []
assert not item.undo_edit()
item.redo_edit()
item.redo_edit()
assert len(item.patches) == 2
item.begin_edit()
assert item.redo == [], "新编辑要清空重做栈"
item.clear_edits()
assert item.patches == []
print("edit history OK")
