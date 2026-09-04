"""
severity.py — Compute a severity score for a detected road defect.

Score is derived from:
  1. Relative bounding-box area (bigger defect = worse)
  2. Detection confidence
  3. Class-specific severity multiplier (e.g. pothole vs small crack)

Returns: ("low" | "medium" | "high", score: int 0-100)
"""

CLASS_SEVERITY = {
    "pothole":            1.2,
    "wet_pothole":        1.3,
    "waterlogging":       1.4,
    "alligator_crack":    1.1,
    "longitudinal_crack": 0.9,
    "transverse_crack":   0.9,
    "road_crack":         1.0,
    "damaged_road":       1.1,
    "crack":              1.0,
    "repair":             0.6,
    "damaged_signboard":  1.0,
    "missing_signboard":  1.2,
    "d00":                0.9,   # RDD2022 label names
    "d10":                0.9,
    "d20":                1.1,
    "d40":                1.2,
    "d43":                0.8,
    "d44":                0.8,
}

SEVERITY_COLORS = {
    "high":   (0, 0, 220),     # Red (BGR)
    "medium": (0, 165, 255),   # Orange
    "low":    (0, 220, 100),   # Green
}


def compute_severity(bbox, conf, frame_w, frame_h, class_name="pothole"):
    """
    bbox       : [x1, y1, x2, y2] in pixels
    conf       : float 0-1
    frame_w/h  : frame dimensions for normalisation
    class_name : detected class label

    Returns: (label: "low" | "medium" | "high", score: int 0-100)
    """
    x1, y1, x2, y2 = bbox
    box_w = max(0, x2 - x1)
    box_h = max(0, y2 - y1)
    rel_area = (box_w * box_h) / max(1.0, float(frame_w * frame_h))

    # Area score: 0-60 points
    area_score = min(60.0, rel_area * 300.0)

    # Confidence score: 0-25 points
    conf_score = conf * 25.0

    # Class multiplier: 0-15 extra points
    multiplier = CLASS_SEVERITY.get(class_name.lower(), 1.0)
    class_bonus = min(15.0, (multiplier - 0.5) * 30.0)

    score = int(area_score + conf_score + class_bonus)
    score = max(0, min(100, score))

    if score >= 60:
        label = "high"
    elif score >= 35:
        label = "medium"
    else:
        label = "low"

    return label, score
