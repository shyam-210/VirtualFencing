from extensions import db
from datetime import datetime

class CameraFence(db.Model):
    __tablename__ = 'camera_fences'
    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.String(50), nullable=False)  # ID or URL of the camera
    line_x1 = db.Column(db.Float, nullable=False)
    line_y1 = db.Column(db.Float, nullable=False)
    line_x2 = db.Column(db.Float, nullable=False)
    line_y2 = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FenceCrossEvent(db.Model):
    __tablename__ = 'fence_cross_events'
    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(200), nullable=False)  # path to saved frame