"""
Geometric helper functions for the VERA Body Module.
Calculates 3D points and distances from MediaPipe landmarks.
"""

import numpy as np

def compute_torso_center(lm):
    """
    Compute the 3D center of the torso using shoulders and hips.
    """
    L_sh = np.array([lm[11].x, lm[11].y, lm[11].z])
    R_sh = np.array([lm[12].x, lm[12].y, lm[12].z])
    L_hp = np.array([lm[23].x, lm[23].y, lm[23].z])
    R_hp = np.array([lm[24].x, lm[24].y, lm[24].z])
    return (L_sh + R_sh + L_hp + R_hp) / 4

def compute_shoulder_width(lm):
    """
    Compute the Euclidean distance between left and right shoulders.
    Used as a normalization factor for scale invariance.
    """
    L_sh = np.array([lm[11].x, lm[11].y, lm[11].z])
    R_sh = np.array([lm[12].x, lm[12].y, lm[12].z])
    return np.linalg.norm(L_sh - R_sh)

def compute_gesture_magnitude(lm, shoulder_width=None):
    """
    Compute the mean distance of wrists from the torso center.
    If shoulder_width is provided, returns the value in 'Shoulder Width Units'.
    """
    torso = compute_torso_center(lm)
    L_wr = np.array([lm[15].x, lm[15].y, lm[15].z])
    R_wr = np.array([lm[16].x, lm[16].y, lm[16].z])

    mag_L = np.linalg.norm(L_wr - torso)
    mag_R = np.linalg.norm(R_wr - torso)

    raw_mag = np.nanmean([mag_L, mag_R])

    if shoulder_width and shoulder_width > 0:
        return raw_mag / shoulder_width
    return raw_mag

def compute_posture_openness(lm):
    """
    Compute the angle of the shoulders relative to the neck.
    """
    L_sh = np.array([lm[11].x, lm[11].y, lm[11].z])
    R_sh = np.array([lm[12].x, lm[12].y, lm[12].z])
    neck = (L_sh + R_sh) / 2

    v1 = L_sh - neck
    v2 = R_sh - neck

    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return np.nan

    angle = np.arccos(np.clip(dot / norm, -1, 1))
    return np.degrees(angle)
