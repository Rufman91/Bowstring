# -*- coding: utf-8 -*-
"""
Created on Tue May 14 14:21:19 2024

@author: ASUS
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt

# Create a synthetic target image (black background with a white square)
target_image = np.zeros((500, 500, 3), dtype=np.uint8)
cv2.rectangle(target_image, (150, 150), (350, 350), (255, 255, 255), -1)

# Create a synthetic template image (white square)
template_image = np.zeros((200, 200, 3), dtype=np.uint8)
cv2.rectangle(template_image, (0, 0), (200, 200), (255, 255, 255), -1)

# Convert images to grayscale
target_image_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
template_image_gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)

# Perform template matching
res = cv2.matchTemplate(target_image_gray, template_image_gray, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
top_left = max_loc
w, h = template_image_gray.shape[::-1]
bottom_right = (top_left[0] + w, top_left[1] + h)

# Calculate center of detected region
center = (top_left[0] + w // 2, top_left[1] + h // 2)

# Draw rectangle around detected region
cv2.rectangle(target_image, top_left, bottom_right, (0, 255, 0), 2)

# Plot results
plt.subplot(1, 2, 1)
plt.title('Target Image')
plt.imshow(cv2.cvtColor(target_image, cv2.COLOR_BGR2RGB))

plt.subplot(1, 2, 2)
plt.title('Template Image')
plt.imshow(cv2.cvtColor(template_image, cv2.COLOR_BGR2RGB))

plt.show()

print("Detected center:", center)
