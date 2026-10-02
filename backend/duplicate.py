import math
import cv2

def haversine_m(lat1, lon1, lat2, lon2):
    r=6371000; p1,p2=math.radians(lat1),math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def image_hash(path):
    im=cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if im is None: return None
    small=cv2.resize(im,(9,8)); diff=small[:,1:]>small[:,:-1]
    return ''.join('1' if x else '0' for x in diff.flatten())

def similar_images(a,b):
    h1,h2=image_hash(a),image_hash(b)
    if not h1 or not h2:return False
    return sum(x!=y for x,y in zip(h1,h2))/len(h1) <= .18

def find_duplicate(db, complaint, image_path, damage_types):
    from .models import Complaint
    if complaint.latitude is None or complaint.longitude is None:return None
    for other in db.query(Complaint).filter(Complaint.is_duplicate.is_(False)).all():
        if other.id == complaint.id or other.latitude is None or other.longitude is None:continue
        if haversine_m(complaint.latitude,complaint.longitude,other.latitude,other.longitude)>75:continue
        if not set(map(str.lower,damage_types)).intersection(map(str.lower,other.damage_types or [])):continue
        if other.original_image and similar_images(image_path,other.original_image):return other
    return None
