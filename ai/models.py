import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class DefectClassificationCNN(nn.Module):
    """
    A transfer-learning CNN classifier based on ResNet-18/MobileNetV3.
    """
    def __init__(self, num_classes=7, backbone="resnet18", pretrained=True):
        super(DefectClassificationCNN, self).__init__()
        self.backbone_name = backbone
        
        if backbone == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            resnet = models.resnet18(weights=weights)
            self.features = nn.Sequential(*list(resnet.children())[:-1]) # pool output
            self.fc = nn.Linear(512, num_classes)
        elif backbone == "mobilenet":
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            mobilenet = models.mobilenet_v3_small(weights=weights)
            self.features = mobilenet.features
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.fc = nn.Sequential(
                nn.Linear(576, 1024),
                nn.Hardswish(),
                nn.Dropout(p=0.2, inplace=True),
                nn.Linear(1024, num_classes)
            )
        else:
            # Fallback custom simple CNN
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2), # 112
                
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2), # 56
                
                nn.Conv2d(64, 128, kernel_size=3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2), # 28
                
                nn.Conv2d(128, 256, kernel_size=3, padding=1),
                nn.BatchNorm2d(256),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2)  # 14
            )
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.features(x)
        if hasattr(self, 'pool'):
            x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x

class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)

class DefectSegmentationUNet(nn.Module):
    """
    A lightweight U-Net architecture for pixel-level defect segmentation/mask generation.
    """
    def __init__(self, in_channels=3, out_channels=1):
        super(DefectSegmentationUNet, self).__init__()
        
        # Encoder (Downsampling)
        self.inc = DoubleConv(in_channels, 64)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(128, 256))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(256, 512))
        
        # Decoder (Upsampling)
        self.up1 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.conv_up1 = DoubleConv(512, 256)
        
        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.conv_up2 = DoubleConv(256, 128)
        
        self.up3 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.conv_up3 = DoubleConv(128, 64)
        
        # Output layer
        self.outc = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        # Encoder
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        
        # Decoder with Skip Connections
        u1 = self.up1(x4)
        # Handle shape differences if any
        if u1.shape != x3.shape:
            diffY = x3.size()[2] - u1.size()[2]
            diffX = x3.size()[3] - u1.size()[3]
            u1 = F.pad(u1, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        m1 = torch.cat([x3, u1], dim=1)
        c1 = self.conv_up1(m1)
        
        u2 = self.up2(c1)
        if u2.shape != x2.shape:
            diffY = x2.size()[2] - u2.size()[2]
            diffX = x2.size()[3] - u2.size()[3]
            u2 = F.pad(u2, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        m2 = torch.cat([x2, u2], dim=1)
        c2 = self.conv_up2(m2)
        
        u3 = self.up3(c2)
        if u3.shape != x1.shape:
            diffY = x1.size()[2] - u3.size()[2]
            diffX = x1.size()[3] - u3.size()[3]
            u3 = F.pad(u3, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        m3 = torch.cat([x1, u3], dim=1)
        c3 = self.conv_up3(m3)
        
        logits = self.outc(c3)
        return torch.sigmoid(logits)
