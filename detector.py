import cv2
import numpy as np
import os
import gc  # garbage collector to free RAM after detection

# COCO class IDs
PERSON_CLASS = 0   # 'person'
CHAIR_CLASS  = 56  # 'chair'
COUCH_CLASS  = 57  # 'couch/sofa'


def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(areaA + areaB - interArea + 1e-6)
    return iou


def is_person_near_chair(person_box, chair_box, iou_threshold=0.1):
    return calculate_iou(person_box, chair_box) > iou_threshold


def run_detection(frame):
    from ultralytics import YOLO  # lazy import - only loads when needed

    # Resize to reduce memory during inference
    frame = cv2.resize(frame, (640, 480))

    # Load model
    model = YOLO("yolov8n.pt")

    # imgsz=320 uses significantly less RAM than default 640
    results = model(frame, verbose=False, imgsz=320)[0]

    person_boxes = []
    chair_boxes  = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        coords = [int(c) for c in box.xyxy[0].tolist()]

        if cls_id == PERSON_CLASS:
            person_boxes.append(coords)
        elif cls_id in (CHAIR_CLASS, COUCH_CLASS):
            chair_boxes.append(coords)

    occupied_count = 0
    free_count     = 0

    for chair in chair_boxes:
        occupied = any(is_person_near_chair(p, chair) for p in person_boxes)

        if occupied:
            occupied_count += 1
            color, label = (0, 0, 255), "Occupied"
        else:
            free_count += 1
            color, label = (0, 255, 0), "Free"

        cv2.rectangle(frame, (chair[0], chair[1]), (chair[2], chair[3]), color, 2)
        cv2.putText(frame, label, (chair[0], chair[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    for person in person_boxes:
        cv2.rectangle(frame, (person[0], person[1]), (person[2], person[3]),
                      (255, 150, 0), 1)

    total_chairs      = len(chair_boxes)
    occupancy_percent = round((occupied_count / total_chairs * 100), 1) if total_chairs > 0 else 0

    summary = f"Free: {free_count}  Occupied: {occupied_count}  Total: {total_chairs}"
    cv2.putText(frame, summary, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    os.makedirs("static/output", exist_ok=True)
    cv2.imwrite("static/output/frame.jpg", frame)

    # Free RAM immediately
    del model
    del results
    gc.collect()

    return frame, {
        "total_chairs":      total_chairs,
        "occupied":          occupied_count,
        "free":              free_count,
        "occupancy_percent": occupancy_percent
    }
