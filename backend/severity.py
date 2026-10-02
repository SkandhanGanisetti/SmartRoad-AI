WEIGHTS = {'pothole': 1.0, 'D40': 1.0, 'alligator crack': .9, 'D20': .9, 'transverse crack': .7, 'D10': .7, 'longitudinal crack': .6, 'D00': .6}
def estimate_severity(detections, coverage):
    if not detections: return {'score': 0, 'level': 'Low', 'priority': 'Low'}
    weight = max((WEIGHTS.get(str(d.get('label','')).lower().replace('_',' '), WEIGHTS.get(str(d.get('label','')).upper(), .6)) for d in detections), default=.6)
    confidence = sum(float(d.get('confidence',0)) for d in detections) / len(detections)
    score = min(100, round(100 * (.42*weight + .25*confidence + .15*min(len(detections)/4,1) + .18*min(coverage/25,1))))
    level = 'Critical' if score >= 80 else 'High' if score >= 60 else 'Moderate' if score >= 30 else 'Low'
    return {'score': score, 'level': level, 'priority': 'Medium' if level == 'Moderate' else level}
