"""Create clearly marked, illustrative complaint records without claiming AI predictions."""
from datetime import datetime, timedelta
from .database import init_db, SessionLocal
from .models import Complaint

SAMPLES=[('Pothole near East Gate',['Pothole'],'High','Assigned',12.9718,77.5942),('Cracking on Lake Road',['Longitudinal Crack'],'Moderate','Reported',12.9781,77.6014),('Surface failure at bus stop',['Pothole'],'Critical','In Progress',12.9652,77.5891),('Alligator cracking, Ward 8',['Alligator Crack'],'High','Verified',12.9823,77.5834),('Transverse crack on Market Street',['Transverse Crack'],'Low','Closed',12.9691,77.6071),('Road damage near school',['Pothole'],'Moderate','Reported',12.9872,77.5952),('Lane edge distress',['Longitudinal Crack'],'Low','Repaired',12.9598,77.5998),('Crack cluster at junction',['Alligator Crack'],'High','Needs Review',12.9738,77.5794)]
def seed():
    init_db(); db=SessionLocal()
    try:
        if db.query(Complaint).filter(Complaint.is_demo.is_(True)).count(): print('Demo records already seeded.'); return
        for i,(title,types,sev,status,lat,lon) in enumerate(SAMPLES):
            db.add(Complaint(ticket_id=f'SR-DEMO-{i+1:03}',title=title,damage_types=types,severity=sev,severity_score={'Low':22,'Moderate':46,'High':72,'Critical':87}[sev],priority='Medium' if sev=='Moderate' else sev,status=status,latitude=lat,longitude=lon,address='Demonstration location',confidence=0,damage_coverage=0,detection_count=0,detection_json=[],is_demo=True,created_at=datetime.utcnow()-timedelta(days=i*2)))
        db.commit(); print(f'Seeded {len(SAMPLES)} illustrative demo complaints (no image or AI predictions).')
    finally: db.close()
if __name__=='__main__': seed()
