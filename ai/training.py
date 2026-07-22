import os
import time
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter
from PIL import Image

from ai.models import DefectClassificationCNN
from ai.augmentation import get_augmentation_pipeline

logger = logging.getLogger("visioninspect.training")

class MVTecDataset(Dataset):
    """
    Custom PyTorch dataset loader for MVTec anomaly classification datasets.
    Maps folders (good, scratch, crack, dent, etc.) to class indices.
    """
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []
        self.labels = []
        
        # Define categories mapping
        self.classes = ["good", "scratch", "crack", "dent", "missing_component", "surface_damage", "misalignment"]
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        
        if not os.path.exists(root_dir):
            logger.warning(f"Dataset root directory does not exist: {root_dir}")
            return
            
        # Traverse categories
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(root, file)
                    # Infer label from path
                    inferred_label = "good"
                    parent_folder = os.path.basename(root).lower()
                    
                    for cls in self.classes:
                        if cls in parent_folder:
                            inferred_label = cls
                            break
                            
                    self.image_paths.append(img_path)
                    self.labels.append(self.class_to_idx[inferred_label])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {e}")
            # Return placeholder tensor on failure
            image = Image.new("RGB", (224, 224), color=(0, 0, 0))
            
        if self.transform:
            image = self.transform(image)
            
        return image, label

class EarlyStopping:
    """
    Early stopping helper to terminate training when validation loss stops improving.
    """
    def __init__(self, patience=5, min_delta=0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

def run_training_pipeline(dataset_path: str, model_type="resnet18", epochs=10, batch_size=16, learning_rate=0.001) -> dict:
    """
    Trains a classification model using transfer learning on the specified dataset.
    """
    start_time = time.time()
    logger.info(f"Starting training pipeline for {model_type} on {dataset_path}...")
    
    # 1. Dataset Split & Dataloaders
    transform = get_augmentation_pipeline()
    full_dataset = MVTecDataset(dataset_path, transform=transform)
    
    if len(full_dataset) == 0:
        return {"status": "failed", "error": "No images found in dataset path."}
        
    train_size = int(0.7 * len(full_dataset))
    val_size = int(0.15 * len(full_dataset))
    test_size = len(full_dataset) - train_size - val_size
    
    train_set, val_set, test_set = random_split(full_dataset, [train_size, val_size, test_size])
    
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)
    
    # 2. Setup Model, Loss, Optimizer, TensorBoard
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DefectClassificationCNN(num_classes=7, backbone=model_type, pretrained=True)
    model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    tb_log_dir = os.path.join("logs", "tensorboard", f"{model_type}_{int(time.time())}")
    writer = SummaryWriter(log_dir=tb_log_dir)
    early_stopping = EarlyStopping(patience=3)
    
    best_acc = 0.0
    checkpoint_dir = os.path.join("models", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, f"{model_type}_best.pth")
    
    # 3. Training Loop
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        epoch_loss = running_loss / len(train_set)
        epoch_acc = correct / total
        
        # Validation Phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
        val_epoch_loss = val_loss / len(val_set)
        val_epoch_acc = val_correct / val_total
        
        # Write to TensorBoard
        writer.add_scalars('Loss', {'train': epoch_loss, 'val': val_epoch_loss}, epoch)
        writer.add_scalars('Accuracy', {'train': epoch_acc, 'val': val_epoch_acc}, epoch)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_acc:.4f} | Val Loss: {val_epoch_loss:.4f}, Val Acc: {val_epoch_acc:.4f}")
        
        # Checkpoint Saving
        if val_epoch_acc > best_acc:
            best_acc = val_epoch_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_epoch_acc,
            }, checkpoint_path)
            logger.info(f"New best model saved to {checkpoint_path} (Val Acc: {val_epoch_acc:.4f})")
            
        # Early Stopping check
        early_stopping(val_epoch_loss)
        if early_stopping.early_stop:
            logger.info("Early stopping triggered. Training ended.")
            break
            
    writer.close()
    
    # 4. Evaluation on Test Set
    model.eval()
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()
            
    test_acc = test_correct / test_total if test_total > 0 else 0.0
    elapsed_time = time.time() - start_time
    
    # Export Model
    export_path = os.path.join("models", f"{model_type}_final.pth")
    torch.save(model.state_dict(), export_path)
    logger.info(f"Training completed in {elapsed_time:.2f}s. Model exported to {export_path}. Test Accuracy: {test_acc:.4f}")
    
    return {
        "status": "success",
        "elapsed_seconds": round(elapsed_time, 2),
        "train_accuracy": round(epoch_acc, 4),
        "val_accuracy": round(val_epoch_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "best_accuracy": round(best_acc, 4),
        "checkpoint_saved": checkpoint_path,
        "model_exported": export_path,
        "tensorboard_log": tb_log_dir
    }
