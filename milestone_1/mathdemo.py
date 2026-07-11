import cv2
import numpy as np

image_path = r"D:\VisionInspect_AI\dataset\mvtec_anomaly_detection\bottle\train\good\000.png"

img = cv2.imread(image_path)

if img is None:
    print("Image not found!")
    exit()

# -----------------------------
# 3x3 Kernel
# -----------------------------
kernel = np.ones((3,3), np.float32) / 9

print("Kernel:")
print(kernel)

# -----------------------------
# Convolution
# -----------------------------
filtered = cv2.filter2D(img, -1, kernel)

# -----------------------------
# Neighbourhood Pixels
# -----------------------------
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

y, x = 100, 100

print("\n3x3 Neighbourhood around (100,100):")
print(gray[y-1:y+2, x-1:x+2])

cv2.imshow("Original", img)
cv2.imshow("Filtered (Convolution)", filtered)

cv2.waitKey(0)
cv2.destroyAllWindows()