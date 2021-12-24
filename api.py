import requests
import settings

def get_proxy_ips(self, supplier_id, batch_id="order_status"):

    url = settings.GET_PROXIES_URL.format(
        supplier_id=supplier_id, batch_id=batch_id
    )
    response = requests.get(url, headers=self._headers)
    res = response.json()
    return res.get("results")