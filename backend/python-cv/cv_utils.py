import numpy as np
import cv2

# --- Constants for Image Processing ---
IMG_SIZE = 256
VECTOR_LENGTH = 128
CONTOUR_POINTS = 57

def _resample_contour(contour: np.ndarray, num_points: int) -> np.ndarray:
    if len(contour) == 0:
        return np.zeros((num_points, 2), dtype=np.float32)

    # Compute normalized distances along the contour
    distances = np.cumsum([np.linalg.norm(contour[i] - contour[i-1]) for i in range(1, len(contour))])
    distances = np.insert(distances, 0, 0)
    if distances[-1] == 0:
        return np.zeros((num_points, 2), dtype=np.float32)
    distances = distances / distances[-1]

    coords = contour.reshape(-1, 2)
    xp = distances
    fp_x = coords[:, 0]
    fp_y = coords[:, 1]

    # Validate array lengths before interpolation
    if len(xp) != len(fp_x) or len(fp_x) != len(fp_y):
        return np.zeros((num_points, 2), dtype=np.float32)

    new_points_dist = np.linspace(0, 1, num_points)

    interp_x = np.interp(new_points_dist, xp, fp_x)
    interp_y = np.interp(new_points_dist, xp, fp_y)

    return np.vstack((interp_x, interp_y)).T

def extract_vector(image_bytes: bytes) -> list[float]:
    """
    Accepts image bytes, processes with OpenCV, and returns a feature vector.
    Returns an empty list if a shape cannot be processed.
    """
    # 1. Read image data into a NumPy array
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        print("Warning: Could not decode image.")
        return []

    # 2. Pre-processing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    _, thresh = cv2.threshold(resized, 200, 255, cv2.THRESH_BINARY_INV)
    
    # 3. Find the largest contour
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("Warning: No contours found in image.")
        return []

    largest_contour = max(contours, key=cv2.contourArea)
    
    # 4. Extract features
    
    # a) Resample contour to fixed number of points and normalize
    resampled = _resample_contour(largest_contour.reshape(-1, 2), CONTOUR_POINTS)
    normalized_contour = (resampled / IMG_SIZE).flatten().tolist()

    # b) Calculate Hu Moments
    moments = cv2.moments(largest_contour)
    hu_moments = cv2.HuMoments(moments).flatten()
    
    # Log-transform Hu moments for scale invariance
    log_hu_moments = [-np.sign(h) * np.log10(abs(h)) if h != 0 else 0 for h in hu_moments]

    # 5. Combine features into a single vector
    feature_vector = normalized_contour + log_hu_moments
    
    # Ensure final vector has a fixed length (pad if necessary)
    final_vector = (feature_vector + [0] * VECTOR_LENGTH)[:VECTOR_LENGTH]

    return final_vector
