from PIL import Image, ImageDraw

def create_icon(filename, size, color=(13, 110, 253)):
    # Create a square image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple clock icon: circle with two hands
    center = size // 2
    radius = size // 3
    # Circle
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), outline=color, width=8)
    # Hour hand
    draw.line((center, center, center, center - radius // 2), fill=color, width=8)
    # Minute hand
    draw.line((center, center, center + radius // 2, center), fill=color, width=6)
    
    img.save(filename, format='PNG')

if __name__ == '__main__':
    create_icon('static/icons/icon-192x192.png', 192)
    create_icon('static/icons/icon-512x512.png', 512)
    print("Icons generated successfully.")
