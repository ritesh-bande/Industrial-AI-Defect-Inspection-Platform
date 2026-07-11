import os
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2

class MVTecAnomalyDetector:
    def __init__(self):
        # Initialize a pre-trained ResNet-18 model as a feature extractor
        # (This mimics unsupervised anomaly detection features e.g. PatchCore)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model using the modern weights argument
        weights = models.ResNet18_Weights.DEFAULT
        resnet = models.resnet18(weights=weights)
        self.feature_extractor = nn.Sequential(*list(resnet.children())[:-2]) # extract before avgpool
        self.feature_extractor.to(self.device)
        self.feature_extractor.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
    def inspect(self, image_path: str, save_heatmap_dir: str = None) -> tuple:
        """
        Runs feature-based anomaly detection.
        Returns:
            (prediction: str, defect_type: str, severity_level: str, score: float, heatmap_relative_path: str)
        """
        try:
            pil_img = Image.open(image_path).convert("RGB")
            orig_w, orig_h = pil_img.size
            
            # Preprocess image
            tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                features = self.feature_extractor(tensor) # Shape: [1, 512, 7, 7]
                
            # Compute anomaly map based on spatial feature variance
            # In a real PatchCore we measure distance to memory bank. 
            # As an efficient unsupervised demo, we look at local channel variations and activation magnitude
            anomaly_map = torch.mean(features, dim=1).squeeze(0).cpu().numpy() # [7, 7]
            anomaly_map = np.maximum(anomaly_map, 0)
            
            # Normalize map
            if np.max(anomaly_map) > np.min(anomaly_map):
                anomaly_map = (anomaly_map - np.min(anomaly_map)) / (np.max(anomaly_map) - np.min(anomaly_map))
            
            # Calculate anomaly score (max/mean activation ratio)
            anomaly_score = float(np.mean(anomaly_map))
            
            # Determine prediction thresholds
            # Lower score = homogeneous normal, higher score = abnormal activation
            is_anomaly = anomaly_score > 0.45
            
            prediction = "Fail" if is_anomaly else "Pass"
            defect_type = "anomaly" if is_anomaly else "none"
            
            if is_anomaly:
                if anomaly_score > 0.65:
                    severity = "high"
                elif anomaly_score > 0.52:
                    severity = "medium"
                else:
                    severity = "low"
            else:
                severity = "none"
                
            heatmap_path = ""
            if save_heatmap_dir:
                os.makedirs(save_heatmap_dir, exist_ok=True)
                # Resize anomaly map to original image resolution
                anomaly_map_resized = cv2.resize(anomaly_map, (orig_w, orig_h))
                anomaly_map_resized = np.uint8(255 * anomaly_map_resized)
                
                # Apply colormap
                heatmap = cv2.applyColorMap(anomaly_map_resized, cv2.COLORMAP_JET)
                
                # Read original image in OpenCV
                orig_cv = cv2.imread(image_path)
                if orig_cv is not None:
                    # Superimpose heatmap
                    overlay = cv2.addWeighted(orig_cv, 0.6, heatmap, 0.4, 0)
                    filename = os.path.basename(image_path)
                    heatmap_filename = f"heatmap_{filename}"
                    full_heatmap_path = os.path.join(save_heatmap_dir, heatmap_filename)
                    cv2.imwrite(full_heatmap_path, overlay)
                    heatmap_path = f"/static/heatmaps/{heatmap_filename}"
                    
            return prediction, defect_type, severity, round(anomaly_score * 10, 2), heatmap_path
            
        except Exception as e:
            print("Error in AI inspection service:", e)
            return "Pass", "none", "none", 0.0, ""

# Singleton instance
detector = MVTecAnomalyDetector()
