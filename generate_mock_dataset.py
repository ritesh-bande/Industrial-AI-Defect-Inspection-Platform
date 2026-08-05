import os
import cv2
import numpy as np

def create_mock_images():
    base_dir = "dataset"
    splits = ["train", "val"]
    classes = ["good", "defect"]
    
    # Define folder structure
    for split in splits:
        for cls in classes:
            os.makedirs(os.path.join(base_dir, split, cls), exist_ok=True)
            
    # Generate mock images
    # Good: clean circle
    # Defect: circle with a black scratch line
    np.random.seed(42)
    
    for split, count in [("train", 20), ("val", 5)]:
        for i in range(count):
            # Good image (smooth grey square with a neat centered white circle)
            good_img = np.zeros((224, 224, 3), dtype=np.uint8)
            good_img[:, :] = [100, 100, 100]  # Grey background
            cv2.circle(good_img, (112, 112), 50, (255, 255, 255), -1)  # Perfect clean circle
            
            # Add noise to simulate real-world capture
            noise = np.random.normal(0, 8, good_img.shape).astype(np.int16)
            good_img = np.clip(good_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            cv2.imwrite(os.path.join(base_dir, split, "good", f"good_{i}.png"), good_img)
            
            # Defect image (same circle, but with a black line representing a scratch/crack defect)
            defect_img = np.zeros((224, 224, 3), dtype=np.uint8)
            defect_img[:, :] = [100, 100, 100]
            cv2.circle(defect_img, (112, 112), 50, (255, 255, 255), -1)
            cv2.line(defect_img, (80, 80), (144, 144), (0, 0, 0), 4)  # Scratch line
            
            # Add noise
            noise = np.random.normal(0, 8, defect_img.shape).astype(np.int16)
            defect_img = np.clip(defect_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            cv2.imwrite(os.path.join(base_dir, split, "defect", f"defect_{i}.png"), defect_img)
            
    print("Mock dataset generated successfully at D:\\VisionInspect_AI\\dataset!")

if __name__ == "__main__":
    create_mock_images()
