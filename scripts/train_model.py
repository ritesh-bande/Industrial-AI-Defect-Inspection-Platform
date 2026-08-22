import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.models import VisionInspectCNN

class MVTecBinaryDataset(Dataset):
    """
    Dataset loader mapping MVTec categories into binary 2-class targets:
    0 = defect (Fail)
    1 = good (Pass)
    """
    def __init__(self, root_dir, target_categories=("carpet", "capsule"), transform=None):
        self.transform = transform
        self.samples = []
        
        dataset_path = Path(root_dir)
        if not dataset_path.exists():
            print(f"Dataset path {root_dir} not found.", flush=True)
            return

        for category_name in target_categories:
            category_dir = dataset_path / category_name
            if not category_dir.exists():
                continue
            
            # Train good
            train_good = category_dir / "train" / "good"
            if train_good.exists():
                for img_p in train_good.rglob("*"):
                    if img_p.is_file() and img_p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                        self.samples.append((str(img_p), 1))  # 1 = good / pass
                        
            # Test good & defects
            test_dir = category_dir / "test"
            if test_dir.exists():
                for defect_dir in test_dir.iterdir():
                    if defect_dir.is_dir():
                        label = 1 if defect_dir.name == "good" else 0  # 0 = defect / fail
                        for img_p in defect_dir.rglob("*"):
                            if img_p.is_file() and img_p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                                self.samples.append((str(img_p), label))
                                
        print(f"Loaded {len(self.samples)} images from {root_dir} ({', '.join(target_categories)})", flush=True)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (0, 0, 0))
            
        if self.transform:
            image = self.transform(image)
            
        return image, label

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training VisionInspectCNN on device: {device}", flush=True)
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = MVTecBinaryDataset("dataset/mvtec_anomaly_detection", transform=transform)
    if len(dataset) == 0:
        print("Error: No training dataset found.", flush=True)
        return

    dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)
    
    model = VisionInspectCNN(num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    
    epochs = 3
    print(f"Starting training for {epochs} epochs...", flush=True)
    
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (preds == labels).sum().item()
            
        acc = correct / total if total > 0 else 0.0
        loss_val = running_loss / total if total > 0 else 0.0
        print(f"Epoch {epoch}/{epochs} - Loss: {loss_val:.4f} - Accuracy: {acc*100:.2f}%", flush=True)
        
    out_dir = os.path.join("backend", "models")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "custom_cnn.pt")
    
    torch.save(model.state_dict(), out_path)
    print(f"SUCCESS: Model weights trained and saved to {out_path}!", flush=True)

if __name__ == "__main__":
    train()
