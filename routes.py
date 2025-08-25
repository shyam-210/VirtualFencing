# routes.py (Final Corrected Version)

from flask import Blueprint, render_template, Response, request, jsonify, url_for
import cv2
import os
from extensions import db
from models import CameraFence, FenceCrossEvent
from flask import current_app
import base64

routes_bp = Blueprint('main', __name__)

# This global will be initialized when the app starts
detection_manager = None

def init_detection_manager(app):
    """Factory to create the detection manager instance."""
    global detection_manager
    from detection_utils import DetectionManager
    detection_manager = DetectionManager(app)

# --- WEB PAGE ROUTES ---

@routes_bp.route('/')
def home():
    return render_template('home.html')

@routes_bp.route('/logs')
def logs():
    with current_app.app_context():
        events = FenceCrossEvent.query.order_by(FenceCrossEvent.timestamp.desc()).all()
    return render_template('logs.html', events=events)

@routes_bp.route('/camera')
def camera():
    cameras = [
        {"id": "0", "name": "Webcam", "active": True},
        # Add your demo_video.mp4 back if you want to test with it
        # {"id": "demo_video.mp4", "name": "Demo Video File", "active": True},
    ]
    return render_template('cameras.html', cameras=cameras)

@routes_bp.route('/camera/<path:cam_id>')
def view_camera(cam_id):
    """This route gets the video's NATIVE resolution for scaling."""
    # <<< FIX #2: Changed current_app to detection_manager.app >>>
    with detection_manager.app.app_context():
        fence = CameraFence.query.filter_by(cam_id=cam_id).first()
        
        video_width, video_height = 640, 480  # Default fallback
        try:
            source = int(cam_id) if cam_id.isdigit() else cam_id
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        except Exception:
            print(f"Could not determine resolution for {cam_id}. Using defaults.")

    return render_template(
        'camera_view.html', 
        cam_id=cam_id, 
        fence=fence, 
        video_width=video_width, 
        video_height=video_height
    )

@routes_bp.route('/saved_snaps')
def saved_snaps():
    """Display all saved intrusion snapshots grouped by date."""
    from collections import defaultdict
    import os

    with detection_manager.app.app_context():
        # Fetch all events ordered by newest first
        events = FenceCrossEvent.query.order_by(FenceCrossEvent.timestamp.desc()).all()

    # Group events by date (YYYY-MM-DD)
    grouped_events = defaultdict(list)
    for event in events:
        date_str = event.timestamp.strftime("%Y-%m-%d")
        grouped_events[date_str].append(event)

    # Sort dates in descending order
    grouped_events = dict(sorted(grouped_events.items(), reverse=True))

    return render_template('saved_snaps.html', grouped_events=grouped_events)

# --- API AND VIDEO STREAMING ---

# In routes.py

# Replace your old save_line function with this one
@routes_bp.route('/save_line/<path:cam_id>', methods=['POST'])
def save_line(cam_id):
    """ This function now handles both saving a new line and resetting (deleting) it. """
    with detection_manager.app.app_context():
        data = request.get_json()
        # Use .get() to safely check for the 'x1' key. It will be null on reset.
        x1 = data.get('x1')

        fence = CameraFence.query.filter_by(cam_id=cam_id).first()

        # If x1 is None, the frontend is asking to reset/delete the fence.
        if x1 is None:
            if fence:
                db.session.delete(fence)
                db.session.commit()
                return jsonify({'message': 'Fence reset successfully!'})
            # If there was no fence to begin with, just confirm.
            return jsonify({'message': 'No fence to reset.'})
        
        # Otherwise, if x1 has a value, we are saving or updating the fence.
        x2, y1, y2 = data['x2'], data['y1'], data['y2']
        if fence:
            # Update existing fence
            fence.line_x1, fence.line_y1, fence.line_x2, fence.line_y2 = x1, y1, x2, y2
        else:
            # Create a new fence
            fence = CameraFence(cam_id=cam_id, line_x1=x1, line_y1=y1, line_x2=x2, line_y2=y2)
            db.session.add(fence)
        
        db.session.commit()
    return jsonify({'message': 'Fence saved successfully!'})


def generate_detected_frames(cam_id):
    """Generator function that yields processed video frames."""
    source = int(cam_id) if cam_id.isdigit() else cam_id
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"Failed to open camera: {source}")
        return

    try:
        fence_data = None
        # <<< FIX #4: This is the most critical change. Use detection_manager.app >>>
        with detection_manager.app.app_context():
            fence_db = CameraFence.query.filter_by(cam_id=str(cam_id)).first()
            if fence_db:
                fence_data = {
                    'line_x1': fence_db.line_x1, 'line_y1': fence_db.line_y1,
                    'line_x2': fence_db.line_x2, 'line_y2': fence_db.line_y2
                }

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            processed_frame = detection_manager.detect_and_track(frame, fence_data, cam_id)
            
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if ret:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        cap.release()
        # Ensure cleanup is called, it's good practice
        if detection_manager:
            detection_manager.cleanup_camera_state(cam_id)


@routes_bp.route('/video_feed_detect/<path:cam_id>')
def video_feed_detect(cam_id):
    return Response(generate_detected_frames(cam_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@routes_bp.route('/snap/<int:snap_id>')
def view_snap(snap_id):
    """Show a single saved snap full-size with enhancement options."""
    with current_app.app_context():
        snap = FenceCrossEvent.query.get_or_404(snap_id)
    return render_template('view_snap.html', snap=snap)


@routes_bp.route('/enhance_snap/<int:snap_id>')
def enhance_snap(snap_id):
    """Enhance an image and return its URL (industry-style)."""
    with current_app.app_context():
        snap = FenceCrossEvent.query.get_or_404(snap_id)

    img_path = os.path.join(current_app.static_folder, snap.image_path)
    if not os.path.exists(img_path):
        return jsonify({'error': 'Image not found'}), 404

    # Create enhanced folder if it doesn't exist
    enhanced_dir = os.path.join(current_app.static_folder, "enhanced_snaps")
    os.makedirs(enhanced_dir, exist_ok=True)

    # Build enhanced filename
    base_name = os.path.basename(snap.image_path)
    enhanced_path = os.path.join(enhanced_dir, f"enhanced_{base_name}")

    # Avoid recomputation if already exists
    if not os.path.exists(enhanced_path):
        img = cv2.imread(img_path)

        # Optional resize
        max_dim = 1024
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale_ratio = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale_ratio), int(h * scale_ratio)))

        # Simple enhancement (OpenCV detailEnhance)
        enhanced = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)
        cv2.imwrite(enhanced_path, enhanced)

    # Return the URL of enhanced image
    enhanced_url = url_for('static', filename=f"enhanced_snaps/enhanced_{base_name}")
    return jsonify({'enhanced_url': enhanced_url})