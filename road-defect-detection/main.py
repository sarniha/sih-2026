"""
main.py — Single-camera Road Defect Detection & Live Backend Pipeline.

Performs real-time YOLO detection, ByteTrack tracking, temporal confirmation,
geometric severity classification, GPS georeferencing, evidence frame extraction,
and live event emission to the SmartBus Command backend.

Usage:
  python main.py --video data/sample.mp4 --gps data/sample_gps.csv --send-backend
  python main.py --video 0  # webcam live stream
"""

import argparse
import json
import os
import time
import cv2

from config import (
    MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    MIN_HITS_CONFIRMATION,
    SEND_TO_BACKEND,
)
from detector import RoadDefectDetector
from gps_utils import GPSTrack
from events import build_defect_event, send_defect_event, save_evidence_snapshot
from video_writer import AnnotatedVideoWriter


def run_pipeline(
    video_path: str,
    gps_path: str = None,
    model_path: str = MODEL_PATH,
    conf: float = CONFIDENCE_THRESHOLD,
    min_hits: int = MIN_HITS_CONFIRMATION,
    outvid: str = None,
    outjson: str = None,
    send_backend: bool = SEND_TO_BACKEND,
):
    print("=========================================================")
    print("  🚌 SmartBus Urban Sensing — Road Defect Detection  ")
    print("=========================================================")
    print(f"  Input Video  : {video_path}")
    print(f"  Model Weights: {model_path}")
    print(f"  GPS Log      : {gps_path if gps_path else 'None (coordinates disabled)'}")
    print(f"  Confidence   : {conf}")
    print(f"  Min Confirm  : {min_hits} frames")
    print(f"  Send Backend : {send_backend}")
    print("---------------------------------------------------------")

    cap = cv2.VideoCapture(int(video_path) if video_path.isdigit() else video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video source: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    gps_track = GPSTrack(gps_path) if gps_path and os.path.exists(gps_path) else None

    writer = None
    if outvid:
        writer = AnnotatedVideoWriter(outvid, fps, width, height)
        print(f"  Recording HUD output video to: {outvid}")

    detector = RoadDefectDetector(
        model_path=model_path,
        conf_threshold=conf,
        min_hits=min_hits,
    )

    confirmed_events = []
    frame_num = 0
    t_start = time.time()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            gps_loc = gps_track.at(frame_num, fps) if gps_track else None
            active_detections, newly_confirmed = detector.process_frame(frame, frame_num)

            for defect in newly_confirmed:
                evidence_url = save_evidence_snapshot(
                    frame=defect["frame_img"],
                    bbox=defect["bbox"],
                    track_id=defect["track_id"],
                    label=defect["class_name"],
                    severity=defect["severity"],
                    conf=defect["confidence"],
                )

                event = build_defect_event(
                    object_id=defect["track_id"],
                    confidence=defect["confidence"],
                    severity=defect["severity"],
                    bbox=defect["bbox"],
                    lon=gps_loc["lon"] if gps_loc else None,
                    lat=gps_loc["lat"] if gps_loc else None,
                    evidence_url=evidence_url,
                    defect_class=defect["class_name"],
                )

                confirmed_events.append(event)
                print(f"[DEFECT CONFIRMED] #{defect['track_id']} {defect['display_name']} "
                      f"| Severity: {defect['severity']} | Conf: {defect['confidence']:.2f}")

                if send_backend:
                    send_defect_event(event)

            if writer:
                writer.draw_and_write(
                    frame=frame,
                    active_tracks=active_detections,
                    confirmed_count=len(confirmed_events),
                    gps_loc=gps_loc,
                    frame_num=frame_num,
                )

            frame_num += 1
            if frame_num % 50 == 0:
                elapsed = time.time() - t_start
                cur_fps = frame_num / max(elapsed, 0.001)
                progress = f"Frame {frame_num}/{total_frames}" if total_frames > 0 else f"Frame {frame_num}"
                print(f"  ⚙️ Processing: {progress} ({cur_fps:.1f} FPS) | Confirmed Defects: {len(confirmed_events)}")

    finally:
        cap.release()
        if writer:
            writer.release()

    total_time = time.time() - t_start
    print("---------------------------------------------------------")
    print(f"🏁 Completed {frame_num} frames in {total_time:.2f}s ({(frame_num / max(total_time, 0.001)):.1f} FPS)")
    print(f"📊 Total Confirmed Road Defects: {len(confirmed_events)}")

    if outjson:
        with open(outjson, "w") as f:
            json.dump(confirmed_events, f, indent=2)
        print(f"💾 Saved events JSON to: {outjson}")

    return confirmed_events


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Road Defect Detection CLI")
    parser.add_argument("--video", default="data/synthetic_test.mp4", help="Video path or webcam index")
    parser.add_argument("--gps", default="data/sample_gps.csv", help="GPS CSV path")
    parser.add_argument("--model", default=MODEL_PATH, help="YOLO model path")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold")
    parser.add_argument("--min-hits", type=int, default=MIN_HITS_CONFIRMATION, help="Frames needed to confirm defect")
    parser.add_argument("--outvid", default=None, help="Output annotated video path")
    parser.add_argument("--out", default=None, help="Output events JSON path")
    parser.add_argument("--send-backend", action="store_true", default=SEND_TO_BACKEND, help="Emit events to backend")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        gps_path=args.gps if os.path.exists(args.gps) else None,
        model_path=args.model,
        conf=args.conf,
        min_hits=args.min_hits,
        outvid=args.outvid,
        outjson=args.out,
        send_backend=args.send_backend,
    )
