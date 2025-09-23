import requests

class CalDAVClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = (username, password)

    def put_event(self, uid, ical_data):
        url = f"{self.base_url}{uid}.ics"
        headers = {"Content-Type": "text/calendar; charset=utf-8"}
        response = requests.put(url, data=ical_data.encode("utf-8"), headers=headers, auth=self.auth)
        return response
