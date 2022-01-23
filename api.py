import requests
import settings
import base64

def get_proxy_ips(self, supplier_id, batch_id="order_status"):
    headers = {
            "Authorization": "Basic "
            + base64.b64encode(
                bytes(
                    "{}:{}".format(
                        'buybot', 'forte1long'
                    ),
                    encoding="raw_unicode_escape",
                )
            ).decode()
        }


    url = settings.GET_PROXIES_URL.format(
        supplier_id=supplier_id, batch_id=batch_id
    )
    response = requests.get(url, headers=headers)
    res = response.json()
    return res.get("results")