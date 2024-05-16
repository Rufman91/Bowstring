import numpy as np
import cv2

def load_images(image_paths):
    images = []
    for path in image_paths:
        image = cv2.imread(path)
        if image is not None:
            images.append(image)
    return images

def phase_correlation(image1, image2):
    image1_gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    image2_gray = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    shift, response = cv2.phaseCorrelate(np.float32(image1_gray), np.float32(image2_gray))
    return shift

def estimate_transformation(points_image, points_afm):
    transformation_matrix, inliers = cv2.estimateAffine2D(np.array(points_image), np.array(points_afm))
    return transformation_matrix

def transform_coordinates(coord, transformation_matrix):
    coord = np.array([coord[0], coord[1], 1])
    transformed_coord = np.dot(transformation_matrix, coord)
    return transformed_coord[:2]