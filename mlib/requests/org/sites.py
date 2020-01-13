########## SITES ############

def create(mist_session, org_id, name, timezone="", country_code="", address="", lat="", lng="", sitegroup_ids="", rftemplate_id="", secpolicy_id="", alarmtemplate_id=""):
    uri = "/api/v1/orgs/%s/sites" % org_id
    body = {
        "name": name,
        "timezone": timezone,
        "country_code": country_code,
        "rftemplate_id": rftemplate_id,
        "secpolicy_id": secpolicy_id,
        "alarmtemplate_id": alarmtemplate_id,
        "latlng": {
            "lat": lat,
            "lng": lng},
        "sitegroup_ids": sitegroup_ids,
        "address": address
    }
    resp = mist_session.mist_post(uri, org_id=org_id, body=body)
    return resp

def update(mist_session, org_id, site_id, body={}):
    uri = "/api/v1/sites/%s" % site_id
    resp = mist_session.mist_put(uri, org_id=org_id, body=body)
    return resp
    
def delete(mist_session, org_id, site_id):
    uri = "/api/v1/sites/%s" % site_id
    resp = mist_session.mist_delete(uri)
    return resp

def get(mist_session, org_id, page=1, limit=100):
    uri = "/api/v1/orgs/%s/sites" % org_id
    resp = mist_session.mist_get(uri, org_id=org_id, page=page, limit=limit)
    return resp

def stats(mist_session, site_id, page=1, limit=100):
    uri = "/api/v1/sites/%s/stats" % site_id
    resp = mist_session.mist_get(uri, page=page, limit=limit)
    return resp

