import cv2
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

def preprocess_image(image_path: str, target_size=(224, 224)) -> dict:
    """
    Executes a complete image preprocessing pipeline.
    Returns a dictionary containing intermediate visualization steps as numpy arrays
    and the final preprocessed tensor ready for model input.
    """
    # 1. Read image using OpenCV (BGR format)
    orig_bgr = cv2.imread(image_path)
    if orig_bgr is None:
        raise ValueError(f"Could not load image at path: {image_path}")
    
    # 2. Resize
    resized_bgr = cv2.resize(orig_bgr, target_size)
    resized_gray = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2GRAY)
    
    # 3. Contrast Enhancement (CLAHE on Gray, or LAB for Color)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(resized_gray)
    
    # Apply to color (Convert to LAB, apply CLAHE to L channel, convert back)
    lab = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_color = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # 4. Noise Reduction (Bilateral filtering keeps edges sharp while smoothing noise)
    denoised_color = cv2.bilateralFilter(enhanced_color, d=9, sigmaColor=75, sigmaSpace=75)
    denoised_gray = cv2.bilateralFilter(enhanced_gray, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 5. Gaussian Blur (Specifically for softening remaining high-frequency noise)
    blurred_color = cv2.GaussianBlur(denoised_color, (5, 5), 0)
    blurred_gray = cv2.GaussianBlur(denoised_gray, (5, 5), 0)
    
    # 6. Edge Detection (Canny)
    edges = cv2.Canny(blurred_gray, threshold1=30, threshold2=100)
    
    # 7. Normalization for PyTorch models
    # Convert BGR to RGB PIL image for standard torchvision transforms
    pil_img = Image.fromarray(cv2.cvtColor(denoised_color, cv2.COLOR_BGR2RGB))
    
    # PyTorch normalization
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    normalized_tensor = transform(pil_img)
    
    return {
        "original": orig_bgr,
        "resized": resized_bgr,
        "enhanced": enhanced_color,
        "denoised": denoised_color,
        "blurred": blurred_color,
        "edges": edges,
        "tensor": normalized_tensor
    }
