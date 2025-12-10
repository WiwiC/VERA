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
    Compute posture openness as the angle formed at the sternum.

    Measures the angle: Left Shoulder - Sternum - Right Shoulder

    - Larger angle (approaching 180°) = open, confident posture
    - Smaller angle = hunched, closed posture

    The sternum is estimated as the midpoint between mid-shoulders and mid-hips.
    This captures whether shoulders are rolled forward (closed) or back (open).
    """
    # Shoulder positions
    L_sh = np.array([lm[11].x, lm[11].y, lm[11].z])
    R_sh = np.array([lm[12].x, lm[12].y, lm[12].z])

    # Hip positions
    L_hp = np.array([lm[23].x, lm[23].y, lm[23].z])
    R_hp = np.array([lm[24].x, lm[24].y, lm[24].z])

    # Estimate sternum: midpoint between shoulder-center and hip-center
    mid_shoulder = (L_sh + R_sh) / 2
    mid_hip = (L_hp + R_hp) / 2
    sternum = (mid_shoulder + mid_hip) / 2

    # Vectors from sternum to each shoulder
    v1 = L_sh - sternum
    v2 = R_sh - sternum

    # Compute angle between these vectors
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)

    if norm == 0:
        return np.nan

    angle = np.arccos(np.clip(dot / norm, -1, 1))
    return np.degrees(angle)


def compute_wrist_depth_norm(lm, shoulder_width):
    """
    Compute normalized wrist depth relative to torso (z-axis).

    Args:
        lm: MediaPipe pose landmarks
        shoulder_width: Shoulder width for normalization

    Returns:
        float: Normalized depth (in shoulder width units)
               Negative = wrists in front of torso
               Positive = wrists behind torso
               Typical values:
                 -0.5 = relaxed arms
                 -1.0 = gesturing forward
                 -1.5 to -2.0 = defensive posture (hands clasped/crossed)
    """
    L_wrist_z = lm[15].z
    R_wrist_z = lm[16].z
    torso_z = (lm[11].z + lm[12].z + lm[23].z + lm[24].z) / 4

    if shoulder_width <= 0:
        return 0.0

    # Normalize depth difference by shoulder width
    depth_L = (L_wrist_z - torso_z) / shoulder_width
    depth_R = (R_wrist_z - torso_z) / shoulder_width

    # Return mean depth (more negative = more forward)
    return (depth_L + depth_R) / 2
