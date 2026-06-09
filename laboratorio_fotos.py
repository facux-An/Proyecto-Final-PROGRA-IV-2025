import os
from PIL import Image, ImageEnhance, ImageDraw, ImageFont

def process_image(input_path, output_path):
    print(f"Procesando: {input_path}")
    try:
        img = Image.open(input_path).convert("RGBA")
    except Exception as e:
        print(f"Error abriendo imagen: {e}")
        return

    # 1. Filtros sutiles (Realidad Aumentada)
    # Calidez suave
    warm_overlay = Image.new('RGBA', img.size, (255, 170, 0, 15))
    img = Image.alpha_composite(img, warm_overlay)
    
    # Convertimos a RGB
    img = img.convert("RGB")
    
    # Contraste y color
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.20)
    
    # 2. Formato 1:1 (Padding Inteligente)
    w, h = img.size
    max_dim = max(w, h)
    
    # Color de fondo (blanco hueso muy claro que se funde bien)
    bg_color = (250, 248, 246)
    square = Image.new('RGB', (max_dim, max_dim), bg_color)
    offset_x = (max_dim - w) // 2
    offset_y = (max_dim - h) // 2
    square.paste(img, (offset_x, offset_y))
    
    # Setup de dibujo (usamos RGBA para tener transparencias si es necesario)
    draw = ImageDraw.Draw(square, 'RGBA')
    
    # 3. Tipografía Integrada (Título Flotante con Drop Shadow)
    title = 'Kit "Hogar Impecable"'
    
    # Buscar una fuente impactante y gruesa
    font_paths = [r"C:\Windows\Fonts\impact.ttf", r"C:\Windows\Fonts\ariblk.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
    font_title = None
    font_size = int(max_dim * 0.08)
    for path in font_paths:
        try:
            font_title = ImageFont.truetype(path, font_size)
            break
        except: continue
    if not font_title: font_title = ImageFont.load_default()
    
    # Calcular ancho para centrar el título
    try:
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
    except:
        tw = font_size * len(title) * 0.6
    
    tx = (max_dim - tw) // 2
    ty = int(max_dim * 0.04) # 4% desde el borde superior
    
    # Drop shadow sutil manual (gris claro)
    draw.text((tx+4, ty+4), title, font=font_title, fill=(200, 200, 200, 180))
    # Texto principal (Gris oscuro estilo premium de la foto de referencia)
    draw.text((tx, ty), title, font=font_title, fill=(70, 70, 70, 255))
    
    # Subtítulo inferior
    subtitle = "Solución Integral para Ropa y Muebles"
    try:
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", int(font_size*0.4))
    except: font_sub = font_title
    try:
        bbox_sub = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox_sub[2] - bbox_sub[0]
    except: sw = font_size * 0.4 * len(subtitle) * 0.6
    sx = (max_dim - sw) // 2
    sy = max_dim - int(max_dim * 0.08)
    draw.text((sx, sy), subtitle, font=font_sub, fill=(100, 100, 100, 255))
    
    # 4. Callouts (Minimalistas) - Textos y líneas apuntando
    try:
        font_callout_bold = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", int(font_size*0.35))
        font_callout_light = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", int(font_size*0.35))
    except:
        font_callout_bold = font_title
        font_callout_light = font_title
        
    line_color = (60, 60, 60, 255)
    
    def draw_callout(cx, cy, target_x, target_y, title_text, desc_text, align):
        # Dibujar la línea desde el texto hasta el punto en el producto
        draw.line([(cx, cy), (target_x, target_y)], fill=line_color, width=4)
        # Dibujar el "puntito" final
        draw.ellipse([target_x-8, target_y-8, target_x+8, target_y+8], fill=line_color)
        
        # Calcular posicion de texto para no chocar con la linea
        if align == "left":
            text_x = int(max_dim * 0.05) # Alineado a la izquierda del cuadro
        else:
            text_x = cx + 20
        text_y = cy - int(font_size*0.8)
        
        draw.text((text_x, text_y), title_text, font=font_callout_bold, fill=line_color)
        draw.text((text_x, text_y + int(font_size*0.45)), desc_text, font=font_callout_light, fill=line_color)

    # Rodillo (Se asume que está a la izquierda de la imagen original)
    target_rollo_x = offset_x + int(w * 0.35)
    target_rollo_y = offset_y + int(h * 0.70)
    cx_rollo = int(max_dim * 0.28)
    cy_rollo = target_rollo_y - int(h * 0.15)
    draw_callout(cx_rollo, cy_rollo, target_rollo_x, target_rollo_y, "1. Rodillo Quita Pelos", "Captura instantánea\nde pelusa y pelo", "left")

    # Cepillo (Se asume que está a la derecha)
    target_cepillo_x = offset_x + int(w * 0.70)
    target_cepillo_y = offset_y + int(h * 0.75)
    cx_cepillo = int(max_dim * 0.75)
    cy_cepillo = target_cepillo_y - int(h * 0.25)
    draw_callout(cx_cepillo, cy_cepillo, target_cepillo_x, target_cepillo_y, "2. Cepillo a Vapor", "Limpieza profunda\ny masajes", "right")

    # Guardar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img = square.convert("RGB")
    final_img.save(output_path, quality=98)
    print(f"¡Éxito! Infografía guardada en: {output_path}")

# Rutas
input_img = r"C:\Users\fandr\Desktop\Fotos de catalogo\original\foto_kit_basico.jpg.jpeg"
output_img = r"C:\Users\fandr\Desktop\Fotos de catalogo\IA\kit_basico_infografia.jpg"

process_image(input_img, output_img)
