from PIL import Image, ImageDraw

SIZE = 256
GRID = 5
GAP = 6
CELL = 32
START = (SIZE - (GRID * CELL + (GRID - 1) * GAP)) // 2

Y = (255, 199, 0)
W = (245, 245, 245)
G = (158, 158, 158)
D = (85, 85, 85)
T = None

MATRIX = [
    [Y, Y, W, W, G],
    [Y, Y, Y, W, G],
    [W, Y, G, G, D],
    [W, G, G, D, D],
    [G, G, D, D, T],
]

SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def make_icon():
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=56, fill=(26, 26, 26, 255))
    for r in range(GRID):
        for c in range(GRID):
            color = MATRIX[r][c]
            if color is None:
                continue
            x = START + c * (CELL + GAP)
            y = START + r * (CELL + GAP)
            d.rounded_rectangle(
                [x, y, x + CELL - 1, y + CELL - 1], radius=6, fill=color + (255,)
            )
    return base


if __name__ == "__main__":
    icon = make_icon()
    icon.save("icon.ico", sizes=SIZES)
    icon.resize((512, 512), Image.Resampling.NEAREST).save("icon_preview.png")
    print("icon.ico + icon_preview.png written")
