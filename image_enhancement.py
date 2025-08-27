import cv2
import numpy as np
import os
import base64

class ImageEnhancer:
    def __init__(self):
        # Initialize face detection cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect_and_enhance_faces(self, image):
        """
        Detect faces in the image and apply targeted enhancement
        """
        # Convert to uint8 for face detection
        temp_img = image.astype(np.uint8)
        gray = cv2.cvtColor(temp_img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        enhanced = image.copy()
        for (x, y, w, h) in faces:
            # Extract face region with margin
            margin = int(0.5 * w)  # 50% margin
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(image.shape[1], x + w + margin)
            y2 = min(image.shape[0], y + h + margin)
            
            face_region = image[y1:y2, x1:x2].copy()
            
            # Enhanced processing for face regions
            enhanced_face = self.enhance_region(face_region, is_face=True)
            enhanced[y1:y2, x1:x2] = enhanced_face
            
        return enhanced

    def enhance_region(self, img, is_face=False):
        """
        Enhanced image processing with special handling for face regions
        """
        # Ensure input is uint8 for initial processing
        img_uint8 = np.clip(img, 0, 255).astype(np.uint8)
        
        # Apply bilateral filter for edge-preserving smoothing
        smooth = cv2.bilateralFilter(img_uint8, 9, 75, 75)
        
        # Convert to float32 for detail extraction
        img_float = img_uint8.astype(np.float32)
        smooth_float = smooth.astype(np.float32)
        detail = img_float - smooth_float
        
        # Enhance local contrast using CLAHE on uint8
        lab = cv2.cvtColor(smooth, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Adaptive CLAHE based on region type (requires uint8)
        if is_face:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        else:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            
        l = clahe.apply(l)  # l is already uint8
        enhanced_lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Convert to float32 for advanced operations
        enhanced_float = enhanced.astype(np.float32)
        
        # Advanced sharpening
        gaussian = cv2.GaussianBlur(enhanced_float, (0, 0), 2.0)
        unsharp_mask = cv2.addWeighted(enhanced_float, 2.0, gaussian, -1.0, 0)
        
        # Add back enhanced details
        detail_weight = 1.5 if is_face else 1.0
        weighted_detail = cv2.multiply(detail, detail_weight)
        result = cv2.add(unsharp_mask, weighted_detail)
        
        # Final contrast adjustment
        min_val = np.min(result)
        max_val = np.max(result)
        if max_val > min_val:
            # Normalize to full range
            result = (result - min_val) * (255.0 / (max_val - min_val))
        
        # Ensure valid range and convert to uint8
        return np.clip(result, 0, 255).astype(np.uint8)
        
    def enhance(self, image_path):
        """
        Enhance an image using advanced CV techniques with face-aware processing
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return None

            # Initial denoising with edge preservation
            denoised = cv2.fastNlMeansDenoisingColored(img, None, 7, 7, 5, 15)
            
            # Detect and enhance faces first
            enhanced = self.detect_and_enhance_faces(denoised)
            
            # Global image enhancement
            enhanced = self.enhance_region(enhanced)

            # Final global adjustments for better visualization
            alpha = 1.1  # Subtle contrast enhancement
            beta = 5     # Slight brightness boost
            final = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

            return final

        except Exception as e:
            print(f"Error enhancing image: {str(e)}")
            return None

# Create a singleton instance
enhancer = ImageEnhancer()

def enhance_image(image_path):
    """
    Global function to enhance an image using the ImageEnhancer class.
    Returns enhanced image as a numpy array, or None if enhancement fails.
    """
    return enhancer.enhance(image_path)
