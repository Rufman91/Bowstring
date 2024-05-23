import numpy as np
import cv2
import logging
from PyQt5.QtGui import QImage


def qimage_to_cv2(qimage):
    qimage = qimage.convertToFormat(QImage.Format_RGB32)
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    arr = np.array(ptr).reshape(height, width, 4)
    return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

def load_images(image_paths):
    images = []
    for path in image_paths:
        logging.debug(f"Loading image from path: {path}")
        image = qimage_to_cv2(QImage(path))
        if image is not None:
            images.append(image)
            logging.debug(f"Loaded image from path: {path}")
        else:
            logging.error(f"Failed to load image from path: {path}")
        print(image.dtype,image.shape)
    return images

def preprocess_image(image):
    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # gray_image = image
    
    # Step 1: Negate the image
    negated_image = cv2.bitwise_not(gray_image)
    
    # Step 2: Apply binary thresholding
    _, binary_image = cv2.threshold(negated_image, 200, 255, cv2.THRESH_BINARY)
    
    # Step 3: Remove small objects using morphological operations
    kernel = np.ones((5, 5), np.uint8)
    opened_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
    
    # Step 4: Find the largest connected component
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(opened_image, connectivity=8)
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])  # Ignore the background
    
    mask = np.zeros_like(labels, dtype=np.uint8)
    mask[labels == largest_label] = 255
    
    # Step 5: Return the cleaned-up binary image
    cleaned_image = cv2.bitwise_and(binary_image, binary_image, mask=mask)
    
    return cleaned_image

def phase_correlation(image1, image2):
    # Preprocess images to isolate the cantilever
    image1_preprocessed = preprocess_image(image1)
    image2_preprocessed = preprocess_image(image2)
    
    # Since preprocess_image already returns grayscale images, no need for additional conversion
    image1_gray = image1_preprocessed
    image2_gray = image2_preprocessed

    # Compute the phase correlation
    shift, response = cv2.phaseCorrelate(np.float32(image1_gray), np.float32(image2_gray))
    
    # Possibly switch the indexing of the shifts
    shift = (-shift[0], -shift[1])
    
    return shift

def estimate_transformation(points_image, points_afm):
    transformation_matrix, inliers = cv2.estimateAffine2D(np.array(points_image), np.array(points_afm))
    return transformation_matrix

def transform_coordinates(coord, transformation_matrix):
    coord = np.array([coord[0], coord[1], 1])
    transformed_coord = np.dot(transformation_matrix, coord)
    return transformed_coord[:2]
