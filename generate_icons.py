#!/usr/bin/env python3
"""Generate PNG icons from the design specifications."""
from PIL import Image, ImageDraw

# Colors from the receipt app
BG_COLOR = '#0a9f8c'  # Teal background
PAPER_COLOR = '#f7fbff'  # Light paper
INK_COLOR = '#0a9f8c'  # Teal text
ACCENT_COLOR = '#0c8f7e'  # Dark teal

def create_icon(size):
    """Create a receipt icon PNG of the specified size."""
    # Create image with teal background
    img = Image.new('RGBA', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Scale factors
    scale = size / 512
    
    # Draw white paper rectangle (receipt)
    paper_left = int(112 * scale)
    paper_top = int(80 * scale)
    paper_right = int((112 + 288) * scale)
    paper_bottom = int((80 + 352) * scale)
    border_radius = int(32 * scale)
    
    # Draw rounded rectangle for paper
    draw.rounded_rectangle(
        [(paper_left, paper_top), (paper_right, paper_bottom)],
        radius=border_radius,
        fill=PAPER_COLOR
    )
    
    # Draw horizontal lines (receipt items)
    line_width = int(24 * scale)
    line_y_positions = [int(170 * scale), int(226 * scale), int(282 * scale)]
    line_left = int(168 * scale)
    
    for y in line_y_positions[:2]:
        line_right = int((168 + 176) * scale)
        draw.line([(line_left, y), (line_right, y)], fill=INK_COLOR, width=max(1, line_width))
    
    # Shorter line for last item
    y = line_y_positions[2]
    line_right = int((168 + 128) * scale)
    draw.line([(line_left, y), (line_right, y)], fill=INK_COLOR, width=max(1, line_width))
    
    # Draw a plus/checkmark circle (completed receipt)
    circle_x = int(320 * scale)
    circle_y = int(336 * scale)
    circle_r = int(56 * scale)
    
    draw.ellipse(
        [(circle_x - circle_r, circle_y - circle_r), (circle_x + circle_r, circle_y + circle_r)],
        fill=ACCENT_COLOR
    )
    
    # Draw small plus/checkmark inside circle
    cross_size = int(16 * scale)
    draw.line(
        [(circle_x - cross_size, circle_y), (circle_x + cross_size, circle_y)],
        fill=PAPER_COLOR,
        width=max(1, int(16 * scale))
    )
    draw.line(
        [(circle_x, circle_y - cross_size), (circle_x, circle_y + cross_size)],
        fill=PAPER_COLOR,
        width=max(1, int(16 * scale))
    )
    
    return img

# Generate icons
print("Generating icons...")
icon_192 = create_icon(192)
icon_512 = create_icon(512)

# Save files
icon_192.save('static/icon-192.png')
icon_512.save('static/icon-512.png')

print("✓ icon-192.png created")
print("✓ icon-512.png created")
