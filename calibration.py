# -*- coding: utf-8 -*-
"""
Created on Tue May 14 10:36:52 2024

@author: Manuel Rufin, Project COSIMA
@institution: Institute of Lightweight Design and Structural Biomechanics, TU Wien, Austria
"""

import os
import numpy as np
import cv2

# Optional: if you need to use PyQt5 for specific image handling tasks
from PyQt5.QtGui import QImage

def load_images(image_paths):
    images = []
    for path in image_paths:
        image = cv2.imread(path)
        if image is not None:
            images.append(image)
    return images

def detect_afm_head(image, template):
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc
    w, h = template_gray.shape[::-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)

    center = (top_left[0] + w // 2, top_left[1] + h // 2)
    return center

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
