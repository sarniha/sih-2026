"""
multi_camera.py — Multi-camera road defect detection & spatial deduplication.

Simulates an urban transit bus equipped with multiple cameras:
  - front: windshield dashcam view
  - rear:  rear road view
  - left/right: side views

Each camera stream is processed in parallel, defects are confirmed temporally,
geo-tagged, cross-camera deduplicated, and dispatched to the command backend.
"""

import argparse
import os
import threading
import queue
import cv2
from typing import Dict, List, Any

from config import (
    MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    MIN_HITS_CONFIRMATION,
    SEND_TO_BACKEND,
)
from detector import RoadDefectDetector
from gps_utils import GPSTrack
from events import build_defect_event, send_defect_event, save_evidence_snapshot
from dedup import deduplicate_events
from video_writer import AnnotatedVideoWriter


class CameraStreamProcessor:
    def __init__(
        self,
        camera_name: str,
        video_source: str,
        model_path: str,
        gps_track: GPSTrack,
        conf_threshold: float,
        outvid_path: str = None,
        event_queue: queue.Queue = None,
    ):
        self.camera_name = camera_name
        self.video_source = video_source
        self.model_path = model_path
        self.gps_track = gps_track
        self.conf_threshold = conf_threshold
        self.outvid_path = outvid_path
        self.event_queue = event_queue
        self.collected_events: List[Dict[str, Any]] = []
        self.thread = threading.Thread(target=self._run, daemon=True, name=f"cam-{camera_name}")

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()

    def _run(self):
        print(f"[{self.camera_name}] 🎬 Initializing stream: {self.video_source}")
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            print(f"[{self.camera_name}] ❌ Could not open video source: {self.video_source}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = None
        if self.outvid_path:
            writer = AnnotatedVideoWriter(self.outvid_path, fps, width, height)

        detector = RoadDefectDetector(
            model_path=self.model_path,
            conf_threshold=self.conf_threshold,
            min_hits=MIN_HITS_CONFIRMATION,
        )

        frame_num = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            gps_loc = self.gps_track.at(frame_num, fps) if self.gps_track else None
            active_detections, newly_confirmed = detector.process_frame(frame, frame_num)

            for defect in newly_confirmed:
                evidence_url = save_evidence_snapshot(
                    frame=defect["frame_img"],
                    bbox=defect["bbox"],
                    track_id=f"{self.camera_name}_{defect['track_id']}",
                    label=defect["class_name"],
                    severity=defect["severity"],
                    conf=defect["confidence"],
                )

                event = build_defect_event(
                    object_id=f"{self.camera_name}_{defect['track_id']}",
                    confidence=defect["confidence"],
                    severity=defect["severity"],
                    bbox=defect["bbox"],
                    lon=gps_loc["lon"] if gps_loc else None,
                    lat=gps_loc["lat"] if gps_loc else None,
                    evidence_url=evidence_url,
                    defect_class=defect["class_name"],
                )
                event["camera_name"] = self.camera_name

                self.collected_events.append(event)
                if self.event_queue:
                    self.event_queue.put(event)

            if writer:
                writer.draw_and_write(
                    frame=frame,
                    active_tracks=active_detections,
                    confirmed_count=len(self.collected_events),
                    gps_loc=gps_loc,
                    frame_num=frame_num,
                )

            frame_num += 1

        cap.release()
        if writer:
            writer.release()
        print(f"[{self.camera_name}] ✅ Completed {frame_num} frames. Confirmed {len(self.collected_events)} defects.")


def run_multi_camera(
    camera_configs: Dict[str, str],
    gps_path: str = None,
    model_path: str = MODEL_PATH,
    conf_threshold: float = CONFIDENCE_THRESHOLD,
    send_backend: bool = SEND_TO_BACKEND,
):
    gps_track = GPSTrack(gps_path) if gps_path else None
    event_queue = queue.Queue()
    processors = []

    for cam_name, video_path in camera_configs.items():
        proc = CameraStreamProcessor(
            camera_name=cam_name,
            video_source=video_path,
            model_path=model_path,
            gps_track=gps_track,
            conf_threshold=conf_threshold,
            event_queue=event_queue,
        )
        processors.append(proc)
        proc.start()

    all_events = []
    for proc in processors:
        proc.join()
        all_events.extend(proc.collected_events)

    print(f"\n⚡ Total multi-camera events detected before deduplication: {len(all_events)}")
    kept, dropped = deduplicate_events(all_events, radius_m=10.0)
    print(f"✅ Deduplication complete: {len(kept)} unique road defects kept, {len(dropped)} cross-camera duplicates merged.")

    if send_backend:
        print(f"🚀 Dispatching {len(kept)} canonical events to backend...")
        for ev in kept:
            send_defect_event(ev)

    return kept


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-camera road defect processor")
    parser.add_argument("--cameras", nargs="+", default=["front=data/test.mp4"],
                        help="Camera mappings in format name=filepath (e.g. front=front.mp4 rear=rear.mp4)")
    parser.add_argument("--gps", default="data/sample_gps.csv", help="GPS track CSV path")
    parser.add_argument("--model", default=MODEL_PATH, help="YOLO model path")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold")
    parser.add_argument("--send-backend", action="store_true", default=SEND_TO_BACKEND, help="Send to central backend")
    args = parser.parse_args()

    cam_dict = {}
    for item in args.cameras:
        if "=" in item:
            k, v = item.split("=", 1)
            cam_dict[k] = v
        else:
            cam_dict[f"cam_{len(cam_dict)}"] = item

    run_multi_camera(
        camera_configs=cam_dict,
        gps_path=args.gps if os.path.exists(args.gps) else None,
        model_path=args.model,
        conf_threshold=args.conf,
        send_backend=args.send_backend,
    )
