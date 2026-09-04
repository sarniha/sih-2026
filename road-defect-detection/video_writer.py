"""
video_writer.py — Annotated output video writer for the road defect pipeline.
Draws real-time bounding boxes, class labels, severity badges, track IDs,
and a HUD overlay (event counter, FPS, GPS coords) on every frame.
"""

import cv2
import time
from severity import SEVERITY_COLORS

HUD_BG       = (20, 20, 20)
HUD_TEXT     = (230, 230, 230)
HUD_ACCENT   = (0, 191, 255)
FONT         = cv2.FONT_HERSHEY_DUPLEX
FONT_SMALL   = 0.45
FONT_MED     = 0.55
FONT_THICK   = 1


class AnnotatedVideoWriter:
    """Wraps cv2.VideoWriter and overlays active tracks + HUD onto each frame."""

    def __init__(self, output_path: str, fps: float, width: int, height: int):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(output_path, fourcc, max(1.0, fps), (width, height))
        self._fps_timer = time.time()
        self._fps_display = 0.0
        self._frame_count = 0

    def annotate_frame(
        self,
        frame,
        active_tracks: list,
        confirmed_count: int,
        gps_loc: dict | None,
        frame_num: int,
    ):
        """Annotate frame with tracks + HUD, returns annotated copy."""
        img = frame.copy()
        h, w = img.shape[:2]

        # Draw each active track
        for trk in active_tracks:
            bbox = trk["bbox"]
            track_id = trk["track_id"]
            conf = trk["confidence"]
            class_name = trk.get("display_name", trk["class_name"])
            sev_label = trk["severity"]
            sev_score = trk["severity_score"]

            x1, y1, x2, y2 = (int(v) for v in bbox)
            color = SEVERITY_COLORS.get(sev_label, (0, 191, 255))

            # Bounding box
            thick = max(2, int(min(w, h) * 0.003))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thick)

            # Label pill
            label = f"#{track_id} {class_name} {conf*100:.0f}%"
            (tw, th), _ = cv2.getTextSize(label, FONT, FONT_MED, FONT_THICK)
            pad = 5
            pill_y1 = max(0, y1 - th - 2 * pad)
            cv2.rectangle(img, (x1, pill_y1), (x1 + tw + 2*pad, y1), color, -1)
            cv2.putText(img, label, (x1 + pad, y1 - pad),
                        FONT, FONT_MED, (255, 255, 255), FONT_THICK, cv2.LINE_AA)

            # Severity badge
            badge = f"{sev_label.upper()} {sev_score}"
            (bw, bh), _ = cv2.getTextSize(badge, FONT, FONT_SMALL, 1)
            bx = max(0, x2 - bw - 2*pad)
            by = min(h - pad, y2 + bh + pad)
            cv2.rectangle(img, (bx - pad, y2), (x2, by + pad), color, -1)
            cv2.putText(img, badge, (bx, by),
                        FONT, FONT_SMALL, (255, 255, 255), 1, cv2.LINE_AA)

        # HUD overlay
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._fps_timer
        if elapsed >= 0.5:
            self._fps_display = self._frame_count / elapsed
            self._fps_timer = now
            self._frame_count = 0

        panel_h = 110
        panel_w = 360
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), HUD_BG, -1)
        img = cv2.addWeighted(overlay, 0.72, img, 0.28, 0)

        lines = [
            ("ROAD DEFECT MONITOR", HUD_ACCENT, FONT_MED),
            (f"Frame: {frame_num:05d}   FPS: {self._fps_display:.1f}", HUD_TEXT, FONT_SMALL),
            (f"Active tracks: {len(active_tracks):3d}   Confirmed: {confirmed_count:3d}", HUD_TEXT, FONT_SMALL),
        ]
        if gps_loc:
            lines.append((f"GPS: {gps_loc['lat']:.6f}, {gps_loc['lon']:.6f}", HUD_TEXT, FONT_SMALL))
        else:
            lines.append(("GPS: (no telemetry)", HUD_TEXT, FONT_SMALL))

        y_offset = 22
        for text, col, scale in lines:
            cv2.putText(img, text, (12, y_offset), FONT, scale, col, FONT_THICK, cv2.LINE_AA)
            y_offset += 22

        return img

    def draw_and_write(
        self,
        frame,
        active_tracks: list,
        confirmed_count: int,
        gps_loc: dict | None,
        frame_num: int,
    ):
        img = self.annotate_frame(frame, active_tracks, confirmed_count, gps_loc, frame_num)
        self._writer.write(img)
        return img

    def release(self):
        self._writer.release()
