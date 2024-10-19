import json
from wsgiref.simple_server import make_server

import falcon

# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
import requests as requests

class BalanceResource:
    def on_get(self, req, resp):
        # Get address from the request
        address = req.get_param('address') or ''
        short_address = address[:12] + '...' + address[-6:]

        if '' == address:
            raise falcon.HTTPBadRequest(
                title="Address is required"
            )

        # Build balance request
        url = 'https://rpc.nano.to'
        post_body = {
            'action': 'account_balance',
            'account': address
        }

        # execute balance request
        try:
            x = requests.post(url, json=post_body)
        except Exception as e:
            raise falcon.HTTPBadRequest(
                title="Failed to retrieve balance",
                description=str(e)
            )

        # Get balance from balance request
        api_resp = json.loads(x.text)
        if 'error' in api_resp:
            raise falcon.HTTPBadRequest(
                title=api_resp['error']
            )
        balance = api_resp['balance'][:-27]
        balance = int(balance) / 1000

        # Build price per coin request
        url = 'https://api.nano.to/price'

        # execute price per coin request
        try:
            x = requests.get(url)
        except Exception:
            raise falcon.HTTPBadRequest(
                title="Failed to retrieve price"
            )

        # handle price per coin request
        api_resp = json.loads(x.text)
        if 'price' not in api_resp:
            raise falcon.HTTPBadRequest(
                title="Failed to retrieve price"
            )
        price = api_resp['price']
        price = round(price, 2)
        usd_balance = price * balance
        usd_balance = round(usd_balance, 2)

        # Build response body
        body = {
            'address': short_address,
            'balance': f'{balance:,}',
            'pricePerCoin': price,
            'USDBalance': f'{usd_balance:,}'
        }

        resp.status = falcon.HTTP_200
        resp.text = json.dumps(body)


# falcon.App instances are callable WSGI apps
# in larger applications the app is created in a separate file
application = falcon.App()

# Resources are represented by long-lived class instances
balance_resource = BalanceResource()

# things will handle all requests to the '/things' URL path
application.add_route('/balance', balance_resource)

# For local testing
if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print('Serving on port 8000...')

        # Serve until process is killed
        httpd.serve_forever()