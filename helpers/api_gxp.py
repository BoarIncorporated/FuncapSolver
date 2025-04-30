import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def Session():
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class Api_GXP:
    def __init__(self):
        self.url = "http://api.sctg.xyz"
        
        self.key = "APIKEY"
        self.max_wait = 300
        self.sleep = 5

    def in_api(self, data):
        session = Session()
        params = {"key": (None, self.key)}
        for key in data:
            params[key] = (None, data[key])
        return session.post(self.url + '/in.php', files=params, verify=False, timeout=15)

    def res_api(self, api_id):
        session = Session()
        params = {"key": self.key, "id": api_id}
        return session.get(self.url + '/res.php', params=params, verify=False, timeout=15)
        
    def get_balance(self):
        session = Session()
        params = {"key": self.key, "action": "getbalance"}
        return session.get(self.url + '/res.php', params=params, verify=False, timeout=15).text

    def run(self, data):
        
        get_in = self.in_api(data)
        if get_in:
            if "|" in get_in.text:
                api_id = get_in.text.split("|")[1]
            else:
                return get_in.text
        else:
            return "ERROR_CAPTCHA_UNSOLVABLE"
        for i in range(self.max_wait//self.sleep):
            time.sleep(self.sleep)
            get_res = self.res_api(api_id)
            if get_res:
                answer = get_res.text
                if 'CAPCHA_NOT_READY' in answer:
                    continue
                elif "|" in answer:
                    return answer.split("|")[1]
                else:
                    return answer