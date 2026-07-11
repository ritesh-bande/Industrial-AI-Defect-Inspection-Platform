import cv2

# -----------------------------
# Read Image
# -----------------------------
image_path = r"D:\VisionInspect_AI\dataset\mvtec_anomaly_detection\bottle\train\good\000.png"

img = cv2.imread(image_path)

if img is None:
    print("❌ Image not found!")
    exit()

print("✅ Image Loaded Successfully!")

# -----------------------------
# Image Properties
# -----------------------------
print("\n--- Image Properties ---")
print("Shape:", img.shape)
print("Height:", img.shape[0])
print("Width:", img.shape[1])
print("Channels:", img.shape[2])

# Display Original Image
cv2.imshow("Original Image", img)
cv2.waitKey(0)

# -----------------------------
# Convert to Grayscale
# -----------------------------
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cv2.imshow("Grayscale Image", gray)
cv2.waitKey(0)

# -----------------------------
# Binary Image
# -----------------------------
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

cv2.imshow("Binary Image", binary)
cv2.waitKey(0)

# -----------------------------
# Pixel Intensity
# -----------------------------
print("\n--- Pixel Values ---")
print("RGB Pixel at (100,100):", img[100,100])
print("Gray Pixel at (100,100):", gray[100,100])

# -----------------------------
# Save Images
# -----------------------------
cv2.imwrite("gray_bottle.png", gray)
cv2.imwrite("binary_bottle.png", binary)

print("\n✅ Images saved successfully!")

cv2.destroyAllWindows()