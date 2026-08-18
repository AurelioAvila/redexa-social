"""Genera icon.ico: un'icona a tema 'rete social' (nodi connessi colorati)."""
from PIL import Image, ImageDraw

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# sfondo rotondo scuro con bordo sfumato
bg_color = (23, 26, 33, 255)
draw.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=56, fill=bg_color)

# nodi (piattaforme social) collegati da linee, stile network/dashboard
nodes = [
    (128, 60, 26, (124, 140, 255)),   # top - blu/viola (accent)
    (60, 130, 22, (244, 114, 182)),   # sx - rosa (instagram-ish)
    (196, 130, 22, (52, 211, 153)),   # dx - verde (whatsapp/growth)
    (95, 200, 20, (251, 191, 36)),    # basso sx - giallo
    (161, 200, 20, (248, 113, 113)),  # basso dx - rosso
]

center = (128, 140)
line_color = (124, 140, 255, 110)
for x, y, r, c in nodes:
    draw.line([center, (x, y)], fill=line_color, width=6)

for x, y, r, c in nodes:
    draw.ellipse([x - r, y - r, x + r, y + r], fill=c)

draw.ellipse([center[0] - 16, center[1] - 16, center[0] + 16, center[1] + 16], fill=(232, 234, 240, 255))

img.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon.ico creata")
