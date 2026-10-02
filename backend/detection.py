from pathlib import Path
import os
import cv2

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / 'ml' / 'best.pt'
_model = None
_model_error = None
LABELS = {'longitudinal_crack':'Longitudinal Crack','transverse_crack':'Transverse Crack','alligator_crack':'Alligator Crack','pothole':'Pothole','D00':'Longitudinal Crack','D10':'Transverse Crack','D20':'Alligator Crack','D40':'Pothole'}

def analyze_image(image_path, run_model=True):
    global _model, _model_error
    image = cv2.imread(str(image_path))
    if image is None: raise ValueError('The uploaded file is not a readable image.')
    h, w = image.shape[:2]; boxes = []
    if run_model:
        if _model is None and MODEL_PATH.exists():
            try:
                from ultralytics import YOLO
                _model = YOLO(str(MODEL_PATH))
            except Exception as exc: _model_error = str(exc)
        if _model is not None:
            try:
                results = _model.predict(image, verbose=False, device='cpu', conf=0.15)
                names = results[0].names
                for box in results[0].boxes:
                    x1,y1,x2,y2 = map(float, box.xyxy[0].tolist()); raw_label = str(names[int(box.cls[0])]); label = LABELS.get(raw_label, LABELS.get(raw_label.upper(), raw_label.replace('_',' ').title()))
                    boxes.append({'label':label,'confidence':round(float(box.conf[0]),4),'bbox':{'x':round(x1,2),'y':round(y1,2),'width':round(x2-x1,2),'height':round(y2-y1,2)}})
            except Exception as exc:
                _model_error = str(exc); _model = None
    overlay = image.copy(); area = 0
    for d in boxes:
        b=d['bbox']; x,y,bw,bh=map(int,(b['x'],b['y'],b['width'],b['height'])); area += max(0,bw)*max(0,bh)
        cv2.rectangle(overlay,(x,y),(x+bw,y+bh),(47,190,117),3); cv2.putText(overlay,f"{d['label']} {d['confidence']:.0%}",(x,max(22,y-8)),cv2.FONT_HERSHEY_SIMPLEX,.65,(47,190,117),2)
    coverage = round(min(100, area/(w*h)*100),2) if w*h else 0
    return {'detections':boxes,'detection_count':len(boxes),'damage_coverage':coverage,'average_confidence':round(sum(x['confidence'] for x in boxes)/len(boxes),4) if boxes else 0,'annotated':overlay,'image_size':{'width':w,'height':h},'model_available':MODEL_PATH.exists() and _model is not None,'model_message': 'RDD model active' if _model is not None else (f'YOLO inference unavailable: {_model_error}' if _model_error else 'No fine-tuned model at ml/best.pt; detector returns no predictions.')}

def detect_road_issues(image_path, model_path=None):
    return analyze_image(image_path)['detections']
