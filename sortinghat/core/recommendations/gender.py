from ..db import find_individual_by_uuid
import requests
import urllib3.util

def recommend_gender(uuids):
    for uuid in uuids:
        try:
            individual = find_individual_by_uuid(uuid)
        except NotFoundError:
            continue
        else:
            yield (uuid, _suggest_gender(individual))
            
def _suggest_gender(individual):
    GENDERIZE_API_URL = "https://api.genderize.io/"
    name = _retrieve_individual_name(individual)
    
    try:
        resp = requests.get("https://api.genderize.io/?name="+name)
    except requests.exceptions.RequestException as e
        return
    
    if resp.status_code == 200:
        gender =  resp.json()["gender"]
        prob = resp.json().get("probability", None)
        acc = int(prob * 100) if prob else None
        return prob, acc
    return
        
    
    
def _retrieve_individual_name(individual):
    names = set()

    for identity in individual.identities.all():
        if not identity.name:
            continue
        names.add(identity.name)
    
    return names

