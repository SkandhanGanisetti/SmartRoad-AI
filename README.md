# SMARTROAD AI
## AI-Based Road Damage Detection, Reporting and Repair Verification System

A local civic infrastructure management demonstrator for recording road damage, triaging complaints, visualizing locations, managing repair status, and comparing before/after images.

### Abstract and problem statement
Road defects can go unreported, be reported multiple times, or remain difficult to prioritize. SMARTROAD AI combines a computer-vision inference service with a small complaint workflow so that a citizen image can become a trackable incident with a location, severity estimate, and repair record. The project is designed for a final-year engineering demonstration and runs locally with SQLite.

### Objectives and features
- Run the included fine-tuned YOLO road damage detector on CPU.
- Annotate images, report damage classes, confidence, detection count, and bounding-box coverage.
- Create unique SR tickets, estimate triage severity, and flag likely duplicates.
- Record complaint status from Reported through Closed, with Duplicate and Needs Review states.
- Compare repair images and report a transparent coverage-based improvement estimate.
- Provide responsive dashboard, complaint register, report form, analytics, and Leaflet map.
- Store complaint and repair metadata in SQLite and uploaded images under `data/`.

### Architecture
React + TypeScript + Vite UI → FastAPI REST API → SQLAlchemy → SQLite. OpenCV reads images and draws boxes; Ultralytics loads `ml/best.pt` lazily on first inference. A missing model never produces synthetic detections: the detector returns an empty list with a model-availability message. The dashboard remains useful for recording and tracking reports, but detection-driven fields require a model.

### Stack
Python, FastAPI, SQLAlchemy, SQLite, Pydantic/FastAPI request validation, OpenCV, NumPy, Ultralytics YOLO; React, TypeScript, Vite, CSS, Lucide React, Leaflet/React Leaflet.

### Database
`users`, `complaints`, and `repairs` are created on backend startup. Complaint rows include ticket, damage, severity, status, coordinates, image paths, model outputs, duplicate linkage, and timestamps. Repair rows store both images, measured coverage, improvement estimate, decision, and notes. Database file: `smartroad.db` at project root.

### Model
The workspace includes the public `dronefreak/rdd2022-yolov8n` checkpoint at `ml/best.pt` (AGPL-3.0 model card). A fresh clone can download it with the command below. The downloader accepts a Hugging Face repository and filename:

```bash
.venv/bin/python -m backend.download_model --repo OWNER/REPOSITORY --filename best.pt
```

The installed checkpoint uses `longitudinal_crack`, `transverse_crack`, `alligator_crack`, and `pothole` class names. Model files are gitignored because they are large. The model card reports mAP@50 58.8 on its held-out public-labelled RDD2022 split; performance varies with country, camera, lighting, and damage size. The checkpoint/model card is AGPL-3.0; review that license for redistribution or deployment.

### Setup
Python 3.14.3 is currently selected by `.venv` (the `python` shell alias is not configured; use `.venv/bin/python`); its installed FastAPI, SQLAlchemy, OpenCV, NumPy, and Ultralytics packages import in this workspace. Python 3.11 is a safer choice if a particular PyTorch checkpoint/runtime does not support your platform. Node and npm are required for the frontend. Dependencies are declared in `requirements.txt` and `frontend/package.json`.

```bash
# Backend dependencies (already installed in this workspace)
.venv/bin/python -m pip install -r requirements.txt

# Terminal 1, project root
.venv/bin/python -m uvicorn backend.main:app --reload --port 8001

# Terminal 2
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:8001` in this workspace (port 8000 was already occupied); set `VITE_API_URL` in `frontend/.env` to override. API documentation: `http://127.0.0.1:8001/docs`.

### Demo data

```bash
.venv/bin/python -m backend.seed_demo
```

The seed creates eight explicitly marked illustrative records with no AI detections, images, confidence, or fabricated predictions. The dashboard map and workflow can be demonstrated before a fresh clone downloads its model checkpoint.

### API endpoints
- `GET /health`
- `POST /api/detect` (multipart `file`)
- `POST /api/complaints` (multipart `title`, `file`, optional `latitude`, `longitude`, `address`)
- `GET /api/complaints`, `GET /api/complaints/{id}`
- `PATCH /api/complaints/{id}/status?status=Assigned`
- `POST /api/complaints/{id}/repair` (multipart `before`, `after`)
- `GET /api/repairs`
- `GET /api/dashboard/stats`
- `GET /api/analytics`

### Workflow
1. Open the dashboard and review counts and map.
2. Choose Report Damage, add title and image, optionally use browser location, submit.
3. The API stores the image, performs inference if the checkpoint exists, adds an annotation, estimates severity, checks nearby matching complaints, and creates an SR ticket.
4. Open the complaint from the register, review detections/duplicate link, and change status.
5. Open Repair Verification, select the ticket, upload before/after images, and read the coverage comparison.

### Duplicate matching
The duplicate check looks for an existing non-duplicate complaint within 75m using Haversine distance, intersects damage labels, then checks a 64-bit OpenCV dHash threshold. Matching reports are saved and marked Duplicate with `duplicate_of` pointing to the original. It is an assistive heuristic, not identity proof.

### Severity and repair verification
Severity is a transparent project heuristic using a class weight, average confidence, detection count, and bounding-box coverage, mapped to Low (0–29), Moderate (30–59), High (60–79), and Critical (80–100). Repair comparison uses the model's total bounding-box coverage reduction; at least 35% improvement and no more than 2% residual box coverage are required for Verified. Otherwise the complaint moves to Needs Review. If the before coverage is zero, the result remains Needs Review because a percentage cannot be meaningfully estimated.

**Important limitation:** The severity and repair verification logic are project-level computer-vision heuristics and are not a replacement for professional road engineering inspection. A bounding box is only a rough proxy for visible damage area.

### Limitations and future work
- The fine-tuned model is present locally but ignored by git due to its size; a fresh clone must download it using the command above.
- Common RDD checkpoint class names are normalized to readable labels; custom checkpoints should use compatible class names for severity and duplicate matching.
- SQLite/local disk are suitable for a demo, not concurrent production use. There is no authentication or role-based access control.
- Geocoding is intentionally omitted; users may enter an address or coordinates.
- Better pixel-level segmentation, calibrated engineering severity, field validation, audit trails, and managed deployment are future work.

### Verification performed
- Backend imports cleanly under Python 3.14.3; `GET /health` returns model availability.
- A public RDD showcase road image produced 3 YOLO detections through both the inference service and live HTTP endpoint.
- API smoke flow passed for detection, complaint create/list, duplicate linkage, status update, repair comparison, dashboard statistics, repairs, and analytics. Temporary smoke records and images were removed; eight marked demo rows remain.
- `npm run build` and `npm run lint` pass. The dashboard and Leaflet map were opened in Chrome and showed the live demo data.
