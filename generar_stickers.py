import os
from PIL import Image, ImageDraw
import math

def create_stickers(source_path, output_path):
    # A4 at 300 DPI
    A4_W, A4_H = 2480, 3508
    canvas = Image.new('RGB', (A4_W, A4_H), 'white')
    draw = ImageDraw.Draw(canvas)

    try:
        logo = Image.open(source_path).convert("RGBA")
    except Exception as e:
        print(f"Could not open {source_path}: {e}")
        return

    # Helper to draw dashed circle and paste logo
    def add_sticker(x, y, diameter):
        r = diameter / 2
        cx, cy = x + r, y + r
        
        # Dibujar línea de corte (gris claro)
        draw.ellipse([x, y, x + diameter, y + diameter], outline="#b0b0b0", width=8)
        
        # Calcular el tamaño del logo dejando un margen interno (sangría)
        padding = int(diameter * 0.12)
        logo_size = diameter - (padding * 2)
        resized_logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Pegar el logo centrado dentro del círculo
        canvas.paste(resized_logo, (int(x + padding), int(y + padding)), resized_logo)

    # --- FILA 1: 12cm = 1417 px ---
    y_pos = 50
    d_12 = 1417
    x_12 = (A4_W - d_12) // 2
    add_sticker(x_12, y_pos, d_12)

    # --- FILA 2: 10cm = 1181 px ---
    y_pos += d_12 + 60
    d_10 = 1181
    gap_10 = 60
    x_10_1 = (A4_W - (d_10 * 2 + gap_10)) // 2
    x_10_2 = x_10_1 + d_10 + gap_10
    add_sticker(x_10_1, y_pos, d_10)
    add_sticker(x_10_2, y_pos, d_10)

    # --- FILA 3: 7cm = 826 px ---
    y_pos += d_10 + 60
    d_7 = 826
    gap_7 = 120
    x_7_1 = (A4_W - (d_7 * 2 + gap_7)) // 2
    x_7_2 = x_7_1 + d_7 + gap_7
    add_sticker(x_7_1, y_pos, d_7)
    add_sticker(x_7_2, y_pos, d_7)

    canvas.save(output_path, quality=98)
    print(f"¡Éxito! Archivo guardado en: {output_path}")

# Buscar la imagen más reciente en Descargas
downloads = r"C:\Users\fandr\Downloads"
files = [f for f in os.listdir(downloads) if f.startswith('magic_edit') and f.endswith('.png')]
files.sort(key=lambda x: os.path.getmtime(os.path.join(downloads, x)), reverse=True)

if files:
    # Asumimos que la primera imagen es el gatito (la última que se descargó al chat)
    source_img = os.path.join(downloads, files[0])
    print(f"Usando imagen base: {source_img}")
    out_file = r"C:\Users\fandr\Desktop\Stickers_TiendaPlus_A4.jpg"
    create_stickers(source_img, out_file)
else:
    print("No se encontró la imagen en Descargas.")
