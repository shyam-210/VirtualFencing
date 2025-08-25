# detection_utils.py

import cv2
from ultralytics import YOLO
import os
from datetime import datetime
from models import FenceCrossEvent
from extensions import db
from shapely.geometry import LineString, Point

class DetectionManager:
    def __init__(self, app):
        self.app = app
        self.model = YOLO("yolov8n.pt")
        # KEY CHANGE: Manage state per camera to avoid conflicts
        self.object_paths = {}      # Stores path history: {cam_id: {track_id: [points]}}
        self.alerted_objects = {}   # Stores alerted IDs: {cam_id: {track_ids}}

    # In detection_utils.py

    def cleanup_camera_state(self, cam_id):
        """
        Resets the tracking data for a camera instead of deleting the key.
        This prevents race conditions when a stream is reloaded.
        """
        # <<< KEY CHANGE: Instead of del, we reset to an empty dict/set >>>
        if cam_id in self.object_paths:
            self.object_paths[cam_id] = {}
        if cam_id in self.alerted_objects:
            self.alerted_objects[cam_id] = set()
        print(f"[INFO] Reset tracking state for camera {cam_id}")

    def detect_and_track(self, frame, fence_data, cam_id):
        """
        Processes a single frame using YOLO's robust tracker and checks for intrusion.
        """
        # Ensure state dictionaries exist for the current camera
        if cam_id not in self.object_paths:
            self.object_paths[cam_id] = {}
            self.alerted_objects[cam_id] = set()

        # KEY CHANGE: Use model.track() for superior object tracking
        results = self.model.track(frame, persist=True, verbose=False, classes=[0]) # class 0 is 'person'
        
        display_frame = results[0].plot()  # YOLO's built-in drawing for boxes and IDs

        fence_line = None
        if fence_data:
            x1, y1 = int(fence_data['line_x1']), int(fence_data['line_y1'])
            x2, y2 = int(fence_data['line_x2']), int(fence_data['line_y2'])
            cv2.line(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            fence_line = LineString([(x1, y1), (x2, y2)])

        # Check for crossings only if a fence and tracked objects exist
        if fence_line and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                # Calculate the center of the bounding box
                center = (int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2))

                # Update the object's path history
                if track_id not in self.object_paths[cam_id]:
                    self.object_paths[cam_id][track_id] = []
                self.object_paths[cam_id][track_id].append(center)
                
                # We need at least two points to define a movement path for the check
                path = self.object_paths[cam_id][track_id]
                if len(path) >= 2:
                    movement_line = LineString([path[-2], path[-1]])
                    
                    # KEY CHANGE: Use robust intersection check and prevent re-alerting
                    if movement_line.intersects(fence_line) and track_id not in self.alerted_objects[cam_id]:
                        self.alerted_objects[cam_id].add(track_id)
                        self._save_snapshot_and_log(frame, center, cam_id, track_id)
        
        return display_frame

    def _save_snapshot_and_log(self, frame, center, cam_id, track_id):
        """Saves a snapshot and logs the event to the database."""
        print(f"[ALERT] Intrusion detected by Object ID {track_id} on Camera {cam_id}!")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = f"intrusion_{cam_id}_{timestamp}_ID{track_id}.jpg"
        
        # Always forward slash for DB storage / URL
        img_rel_path = f"intrusion_snaps/{img_name}"
        
        # Full path for saving image to static folder (os.join works for Windows/Linux)
        img_full_path = os.path.join('static', 'intrusion_snaps', img_name)
        
        # Draw on snapshot
        snapshot = frame.copy()
        cv2.circle(snapshot, center, 10, (0, 0, 255), -1)
        cv2.putText(snapshot, f"INTRUSION ID:{track_id}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Save image
        cv2.imwrite(img_full_path, snapshot)
        print(f"[INFO] Intrusion snapshot saved: {img_full_path}")

        # Save to DB
        try:
            with self.app.app_context():
                event = FenceCrossEvent(cam_id=str(cam_id), image_path=img_rel_path)
                db.session.add(event)
                db.session.commit()
                print(f"[INFO] Intrusion event logged for cam {cam_id}")
        except Exception as e:
            print(f"[ERROR] Failed to log intrusion to database: {e}")
