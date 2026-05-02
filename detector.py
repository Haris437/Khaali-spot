import cv2
import numpy as np
from ultralytics import YOLO
import os

# Load the YOLOv8 nano model (downloads automatically on first run)
model = YOLO("yolov8n.pt")

# COCO class IDs we care about
PERSON_CLASS = 0   # 'person' in COCO
CHAIR_CLASS  = 56  # 'chair' in COCO
COUCH_CLASS  = 57


def calculate_iou(boxA, boxB):
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    Each box is [x1, y1, x2, y2].
    Returns a float between 0 and 1.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Area of intersection
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    # Area of each box
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # IoU formula
    iou = interArea / float(areaA + areaB - interArea + 1e-6)
    return iou


def is_person_near_chair(person_box, chair_box, iou_threshold=0.1):
    """
    Returns True if a person bounding box overlaps with a chair bounding box
    beyond the given IoU threshold. A low threshold (0.1) works well because
    a seated person may only partially overlap the chair bounding box.
    """
    return calculate_iou(person_box, chair_box) > iou_threshold


def run_detection(frame):
    """
    Main detection function.
    
    Args:
        frame: A BGR image (numpy array) from OpenCV.
    
    Returns:
        annotated_frame: The image with bounding boxes drawn.
        stats: A dict with total_chairs, occupied, free, occupancy_percent.
    """
    # Run YOLO inference on the frame
    results = model(frame, verbose=False)[0]

    person_boxes = []
    chair_boxes  = []

    # Separate detections into persons and chairs
    for box in results.boxes:
        cls_id = int(box.cls[0])
        coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
        coords = [int(c) for c in coords]

        if cls_id == PERSON_CLASS:
            person_boxes.append(coords)
        elif cls_id == CHAIR_CLASS or cls_id == COUCH_CLASS:
            chair_boxes.append(coords)

    # Classify each chair as OCCUPIED or FREE
    occupied_count = 0
    free_count      = 0

    for chair in chair_boxes:
        occupied = False
        for person in person_boxes:
            if is_person_near_chair(person, chair):
                occupied = True
                break

        if occupied:
            occupied_count += 1
            color = (0, 0, 255)    # Red  = Occupied
            label = "Occupied"
        else:
            free_count += 1
            color = (0, 255, 0)    # Green = Free
            label = "Free"

        # Draw chair bounding box
        cv2.rectangle(frame, (chair[0], chair[1]), (chair[2], chair[3]), color, 2)
        cv2.putText(frame, label, (chair[0], chair[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Draw person bounding boxes in blue for reference
    for person in person_boxes:
        cv2.rectangle(frame, (person[0], person[1]), (person[2], person[3]),
                      (255, 150, 0), 1)

    total_chairs      = len(chair_boxes)
    occupancy_percent = round((occupied_count / total_chairs * 100), 1) if total_chairs > 0 else 0

    # Overlay summary text on the frame
    summary = f"Free: {free_count}  Occupied: {occupied_count}  Total: {total_chairs}"
    cv2.putText(frame, summary, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Save the annotated frame so Flask can serve it
    os.makedirs("static/output", exist_ok=True)
    cv2.imwrite("static/output/frame.jpg", frame)

    stats = {
        "total_chairs":      total_chairs,
        "occupied":          occupied_count,
        "free":              free_count,
        "occupancy_percent": occupancy_percent
    }

    return frame, stats
