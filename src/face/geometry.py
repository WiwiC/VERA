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


def compute_head_tilt(lm, img_w=640, img_h=480):
    """
    Compute head pitch angle using 3D pose estimation (solvePnP).

    Uses 6 key landmarks to estimate 3D head orientation, then extracts
    the pitch angle (rotation around X-axis).

    Args:
        lm: MediaPipe face landmarks
        img_w: Image width (for 2D point projection)
        img_h: Image height (for 2D point projection)

    Returns:
        float: Head pitch angle in degrees.
               Positive = head tilted down, Negative = head tilted up.
    """
    import cv2

    # 3D model points (canonical face model in arbitrary units)
    # These are approximate 3D coordinates of facial landmarks
    model_points = np.array([
        [0.0, 0.0, 0.0],        # Nose tip (landmark 1)
        [0.0, -63.6, -12.5],    # Chin (landmark 152)
        [-43.3, 32.7, -26.0],   # Left eye outer corner (landmark 33)
        [43.3, 32.7, -26.0],    # Right eye outer corner (landmark 263)
        [-28.9, -28.9, -24.1],  # Left mouth corner (landmark 61)
        [28.9, -28.9, -24.1],   # Right mouth corner (landmark 291)
    ], dtype=np.float64)

    # 2D image points from landmarks
    image_points = np.array([
        [lm[1].x * img_w, lm[1].y * img_h],      # Nose tip
        [lm[152].x * img_w, lm[152].y * img_h],  # Chin
        [lm[33].x * img_w, lm[33].y * img_h],    # Left eye outer
        [lm[263].x * img_w, lm[263].y * img_h],  # Right eye outer
        [lm[61].x * img_w, lm[61].y * img_h],    # Left mouth corner
        [lm[291].x * img_w, lm[291].y * img_h],  # Right mouth corner
    ], dtype=np.float64)

    # Camera matrix (approximate, assuming centered principal point)
    focal_length = img_w
    center = (img_w / 2, img_h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    # Assume no lens distortion
    dist_coeffs = np.zeros((4, 1))

    # Solve PnP to get rotation and translation vectors
    success, rotation_vec, translation_vec = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0  # Fallback if solvePnP fails

    # Convert rotation vector to rotation matrix
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)

    # Extract Euler angles from rotation matrix
    # Using decomposition: R = Rz * Ry * Rx
    sy = np.sqrt(rotation_mat[0, 0]**2 + rotation_mat[1, 0]**2)

    if sy > 1e-6:
        pitch = np.arctan2(-rotation_mat[2, 0], sy)
    else:
        pitch = np.arctan2(-rotation_mat[2, 0], sy)

    # Convert to degrees
    pitch_degrees = np.degrees(pitch)

    # MediaPipe coordinate system: positive pitch = looking down
    return pitch_degrees
