# Ollama expects image inputs to be passed as base64-encoded strings within its API payload.
# We will create a robust file utility function to safely load and encode local images.

import base64
import os
from io import BytesIO
from PIL import Image

def encode_image_to_base64(image_path: str, max_size: int = 1024) -> str:
    """Reads a local image, resizes it to reduce token bloat, and converts to base64."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Evidence image not found at path: {image_path}")
    
    with Image.open(image_path) as img:
        # Convert transparent or paletted images to standard RGB for clean JPEG saving
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Dynamically scale down the image while maintaining aspect ratio
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save compressed image into memory buffer
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        
        # Encode the compressed buffer
        return base64.b64encode(buffer.getvalue()).decode('utf-8')