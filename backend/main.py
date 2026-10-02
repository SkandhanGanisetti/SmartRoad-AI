from datetime import datetime
from pathlib import Path
import uuid
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import get_db, init_db
from .models import Complaint, Repair
from .detection import analyze_image
from .severity import estimate_severity
from .duplicate import find_duplicate
from .verification import verify_coverage

ROOT=Path(__file__).resolve().parent.parent; UPLOADS=ROOT/'data'/'uploads'; REPAIRS=ROOT/'data'/'repairs'
UPLOADS.mkdir(parents=True,exist_ok=True); REPAIRS.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='SMARTROAD AI', description='Road damage reporting and repair verification', version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_methods=['*'],allow_headers=['*'])
app.mount('/media',StaticFiles(directory=str(ROOT/'data')),name='media')
@app.on_event('startup')
def startup(): init_db()
@app.get('/health')
def health(): return {'status':'ok','service':'smartroad-ai','model_present':(ROOT/'ml'/'best.pt').exists()}
def public(c):
    return {'id':c.id,'ticket_id':c.ticket_id,'title':c.title,'damage_types':c.damage_types or [],'severity':c.severity,'severity_score':c.severity_score,'priority':c.priority,'status':c.status,'latitude':c.latitude,'longitude':c.longitude,'address':c.address,'original_image':f"/media/uploads/{Path(c.original_image).name}" if c.original_image else None,'annotated_image':f"/media/uploads/{Path(c.annotated_image).name}" if c.annotated_image else None,'confidence':c.confidence,'damage_coverage':c.damage_coverage,'detection_count':c.detection_count,'detection_json':c.detection_json or [],'is_duplicate':c.is_duplicate,'duplicate_of':c.duplicate_of,'is_demo':c.is_demo,'created_at':c.created_at.isoformat() if c.created_at else None,'updated_at':c.updated_at.isoformat() if c.updated_at else None}
def store_upload(upload, directory):
    suffix=Path(upload.filename or 'image.jpg').suffix.lower()
    if suffix not in {'.jpg','.jpeg','.png','.webp'}: raise HTTPException(400,'Upload a JPG, PNG, or WEBP image.')
    name=f'{uuid.uuid4().hex}{suffix}'; path=directory/name; path.write_bytes(upload.file.read()); return path
@app.post('/api/detect')
async def detect(file: UploadFile=File(...)):
    path=store_upload(file,UPLOADS)
    try: result=analyze_image(path)
    except ValueError as e: path.unlink(missing_ok=True); raise HTTPException(400,str(e))
    annotated=path.with_name(path.stem+'-annotated.jpg'); import cv2; cv2.imwrite(str(annotated),result.pop('annotated')); result['annotated_image']=f'/media/uploads/{annotated.name}'; result.pop('image_size'); return result
@app.post('/api/complaints')
async def create_complaint(title:str=Form(...), latitude:float|None=Form(None), longitude:float|None=Form(None), address:str=Form(''), file:UploadFile=File(...), db:Session=Depends(get_db)):
    path=store_upload(file,UPLOADS)
    try: result=analyze_image(path)
    except ValueError as e: path.unlink(missing_ok=True); raise HTTPException(400,str(e))
    annotated=path.with_name(path.stem+'-annotated.jpg'); import cv2; cv2.imwrite(str(annotated),result['annotated'])
    types=sorted(set(d['label'] for d in result['detections']))
    sev=estimate_severity(result['detections'],result['damage_coverage'])
    ticket='SR-'+datetime.now().strftime('%Y%m%d')+'-'+uuid.uuid4().hex[:6].upper()
    c=Complaint(ticket_id=ticket,title=title,damage_types=types,severity=sev['level'],severity_score=sev['score'],priority=sev['priority'],latitude=latitude,longitude=longitude,address=address,original_image=str(path),annotated_image=str(annotated),confidence=result['average_confidence'],damage_coverage=result['damage_coverage'],detection_count=result['detection_count'],detection_json=result['detections'])
    db.add(c); db.flush(); duplicate=find_duplicate(db,c,path,types)
    if duplicate: c.is_duplicate=True; c.duplicate_of=duplicate.id; c.status='Duplicate'
    db.commit();db.refresh(c);return {**public(c),'model_available':result['model_available'],'model_message':result['model_message']}
@app.get('/api/complaints')
def list_complaints(db:Session=Depends(get_db)):return [public(c) for c in db.query(Complaint).order_by(Complaint.created_at.desc()).all()]
@app.get('/api/complaints/{cid}')
def get_complaint(cid:int,db:Session=Depends(get_db)):
    c=db.get(Complaint,cid)
    if not c:raise HTTPException(404,'Complaint not found')
    return {**public(c),'repairs':[{'id':r.id,'before_image':r.before_image,'after_image':r.after_image,'improvement_percent':r.improvement_percent,'verification_status':r.verification_status,'verification_notes':r.verification_notes} for r in c.repairs]}
@app.patch('/api/complaints/{cid}/status')
def update_status(cid:int,status:str,db:Session=Depends(get_db)):
    allowed={'Reported','Verified','Assigned','In Progress','Repaired','Closed','Needs Review','Duplicate'}
    c=db.get(Complaint,cid)
    if not c:raise HTTPException(404,'Complaint not found')
    if status not in allowed:raise HTTPException(400,f'Status must be one of {", ".join(sorted(allowed))}')
    c.status=status;db.commit();db.refresh(c);return public(c)
@app.post('/api/complaints/{cid}/repair')
async def repair(cid:int,before:UploadFile=File(...),after:UploadFile=File(...),db:Session=Depends(get_db)):
    c=db.get(Complaint,cid)
    if not c:raise HTTPException(404,'Complaint not found')
    bp=store_upload(before,REPAIRS);ap=store_upload(after,REPAIRS)
    try:b=analyze_image(bp);a=analyze_image(ap)
    except ValueError as e:raise HTTPException(400,str(e))
    v=verify_coverage(b['damage_coverage'],a['damage_coverage'])
    import cv2
    ba=bp.with_name(bp.stem+'-annotated.jpg'); aa=ap.with_name(ap.stem+'-annotated.jpg')
    cv2.imwrite(str(ba),b['annotated']); cv2.imwrite(str(aa),a['annotated'])
    row=Repair(complaint_id=cid,before_image=str(bp),after_image=str(ap),before_annotated=str(ba),after_annotated=str(aa),before_coverage=b['damage_coverage'],after_coverage=a['damage_coverage'],improvement_percent=v['improvement_percent'],verification_status=v['status'],verification_notes=v['notes'],verified_at=datetime.utcnow())
    db.add(row)
    if v['status']=='Verified':c.status='Repaired'
    else:c.status='Needs Review'
    db.commit();db.refresh(row)
    return {'id':row.id,'complaint_id':cid,'before_coverage':row.before_coverage,'after_coverage':row.after_coverage,'improvement_percent':row.improvement_percent,'verification_status':row.verification_status,'verification_notes':row.verification_notes,'before_image':f'/media/repairs/{bp.name}','after_image':f'/media/repairs/{ap.name}','before_annotated':f'/media/repairs/{ba.name}','after_annotated':f'/media/repairs/{aa.name}','before_detections':b['detections'],'after_detections':a['detections'],'model_available':b['model_available'] and a['model_available']}
@app.get('/api/repairs')
def list_repairs(db:Session=Depends(get_db)):
    rows=db.query(Repair).order_by(Repair.created_at.desc()).all()
    return [{'id':r.id,'complaint_id':r.complaint_id,'before_image':f'/media/repairs/{Path(r.before_image).name}' if r.before_image else None,'before_annotated':f'/media/repairs/{Path(r.before_annotated).name}' if r.before_annotated else None,'after_image':f'/media/repairs/{Path(r.after_image).name}' if r.after_image else None,'after_annotated':f'/media/repairs/{Path(r.after_annotated).name}' if r.after_annotated else None,'before_coverage':r.before_coverage,'after_coverage':r.after_coverage,'improvement_percent':r.improvement_percent,'verification_status':r.verification_status,'verification_notes':r.verification_notes,'verified_at':r.verified_at.isoformat() if r.verified_at else None} for r in rows]
@app.get('/api/dashboard/stats')
def stats(db:Session=Depends(get_db)):
    rows=db.query(Complaint).all();return {'total_complaints':len(rows),'open_complaints':sum(c.status not in {'Closed','Repaired'} for c in rows),'critical':sum(c.severity=='Critical' for c in rows),'repaired':sum(c.status in {'Repaired','Closed'} for c in rows),'duplicates':sum(c.is_duplicate for c in rows),'avg_severity':round(sum(c.severity_score for c in rows)/len(rows),1) if rows else 0}
@app.get('/api/analytics')
def analytics(db:Session=Depends(get_db)):
    rows=db.query(Complaint).all(); repairs=db.query(Repair).all()
    damage_types=sorted(set(x for c in rows for x in (c.damage_types or [])))
    return {'by_status':_count(rows,'status'),'by_severity':_count(rows,'severity'),'by_damage':{d:sum(d in (c.damage_types or []) for c in rows) for d in damage_types},'repairs':{'total':len(repairs),'verified':sum(r.verification_status=='Verified' for r in repairs),'needs_review':sum(r.verification_status=='Needs Review' for r in repairs)},'recent':[public(c) for c in sorted(rows,key=lambda c:c.created_at or datetime.min,reverse=True)[:7]]}
def _count(rows,attr):
    out={}
    for c in rows:out[getattr(c,attr)]=out.get(getattr(c,attr),0)+1
    return out
