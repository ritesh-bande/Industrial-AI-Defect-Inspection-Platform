import random
import torch
import torchvision.transforms as T
from PIL import Image

def get_augmentation_pipeline(target_size=(224, 224)) -> T.Compose:
    """
    Returns a torchvision transforms pipeline for training data augmentation.
    """
    return T.Compose([
        # Random Rotation between -30 and 30 degrees
        T.RandomRotation(degrees=(-30, 30)),
        
        # Horizontal and Vertical Flips
        T.RandomHorizontalFlip(p=0.5),
        T.RandomVerticalFlip(p=0.5),
        
        # Color Jitter (Brightness, Contrast, Saturation, Hue)
        T.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2,
            hue=0.1
        ),
        
        # Random resized crop (Zoom + Random Crop)
        T.RandomResizedCrop(
            size=target_size,
            scale=(0.8, 1.0),
            ratio=(0.9, 1.1)
        ),
        
        # Convert to tensor and apply standard ImageNet normalization
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

def augment_single_image(pil_image: Image.Image, target_size=(224, 224)) -> Image.Image:
    """
    Applies simple random transformations to a single PIL image
    and returns a PIL image for inspection or saving.
    """
    w, h = pil_image.size
    
    # 1. Random Rotation
    angle = random.uniform(-25, 25)
    img = pil_image.rotate(angle)
    
    # 2. Random Flips
    if random.random() > 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if random.random() > 0.5:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
    # 3. Random Zoom & Crop
    if random.random() > 0.3:
        zoom_factor = random.uniform(0.8, 0.95)
        new_w, new_h = int(w * zoom_factor), int(h * zoom_factor)
        left = random.randint(0, w - new_w)
        top = random.randint(0, h - new_h)
        img = img.crop((left, top, left + new_w, top + new_h))
        img = img.resize(target_size)
        
    # 4. Color jitter
    enhancer = T.ColorJitter(brightness=0.15, contrast=0.15)
    img = enhancer(img)
    
    return img
