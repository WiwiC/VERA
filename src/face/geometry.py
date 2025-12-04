"""
Geometric helper functions for the VERA Face Module.
Calculates 3D points and distances from MediaPipe landmarks.
"""

import numpy as np

def compute_head_center(lm):
    """
    Compute the 3D head center using the left and right ear landmarks.
    """
    left_ear  = np.array([lm[234].x, lm[234].y, lm[234].z])
    right_ear = np.array([lm[454].x, lm[454].y, lm[454].z])
    return (left_ear + right_ear) / 2

def compute_iris_centers(lm):
    """
    Compute the 3D midpoint between the left and right iris centers.
    """
    left_iris = np.array([lm[468].x, lm[468].y, lm[468].z])
    right_iris = np.array([lm[473].x, lm[473].y, lm[473].z])
    return (left_iris + right_iris) / 2

def compute_inter_ocular_distance(lm):
    """
    Compute the Euclidean distance between left and right irises.
    Used as a normalization factor (IOD) for scale invariance.
    """
    left_iris = np.array([lm[468].x, lm[468].y, lm[468].z])
    right_iris = np.array([lm[473].x, lm[473].y, lm[473].z])
    return np.linalg.norm(left_iris - right_iris)

def compute_face_center(lm):
    """
    Compute a stable 3D anchor point on the face, using the nose bridge landmark.
    """
    nose = np.array([lm[1].x, lm[1].y, lm[1].z])
    return nose

def compute_smile_activation(lm):
    """
    Compute smile activation as the Euclidean distance
    between left and right lip corners.
    """
    left = np.array([lm[61].x, lm[61].y, lm[61].z])
    right = np.array([lm[291].x, lm[291].y, lm[291].z])

    return np.linalg.norm(left - right)
