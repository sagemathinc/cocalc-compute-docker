#!/usr/bin/env python3
"""
- Periodically check in with cocalc saying that the server is alive.

- Response message may contain vpn and storage; if so, we update them.


The check_in function below calls the remote API, similar to doing the following using curl from the command line

  curl -sk -u sk-eTUKbl2lkP9TgvFJ00001n: -d '{"id":"13","vpn_sha1":"fbdad59e0793e11ffa464834c647db93d1f9ec99","storage_sha1":"97d170e1550eee4afc0af065b78cda302a97674c"}' -H 'Content-Type: application/json' https://cocalc.com/api/v2/compute/check-in

However, instead of using curl, it uses the requests python library.

Here:
   - the api key like 'sk-eTUKbl2lkP9TgvFJ00001n' is in the file '/cocalc/conf/api_key'
   - storage_sha1 and vpn_sha1 are global variables defined above
   - the api server https://cocalc.com is in the file '/cocalc/conf/api_server'
   - the id is in the file /cocalc/conf/compute_server_id and shold be read from there.
   - the api_key and api_server and id will not change -- they only have to be read from the file once at script startup

The API response is json formatted has optional fields:
   - vpn
   - vpn_sha1
   - storage
   - storage_sha1
They should be used to update the above global variables whenever the sha1 changes.
Also, when vpn change, it should be written as valid json to the file /cocalc/conf/vpn.json,
and when storage changes, write it /cocalc/conf/storage.json.

"""
import datetime, json, sys, time, requests
from requests.auth import HTTPBasicAuth

# by default, ping server every 30s. This parameter should
# be passed in as a command line arg.
period_s = 30

vpn_sha1 = ''
vpn = []
storage = []
storage_sha1 = ''
api_key = ''
api_server = ''
server_id = 0


def check_in():
    global vpn_sha1, vpn, storage_sha1, storage, api_key, api_server, server_id

    try:
        # Read API key, server, and id if needed
        if not api_key:
            api_key = open('/cocalc/conf/api_key', 'r').read().strip()
        if not api_server:
            api_server = open('/cocalc/conf/api_server', 'r').read().strip()
        if not server_id:
            server_id = open('/cocalc/conf/compute_server_id',
                             'r').read().strip()

        # Prepare the request data
        data = {
            "id": server_id,
            "vpn_sha1": vpn_sha1,
            "storage_sha1": storage_sha1
        }

        headers = {
            'Content-Type': 'application/json',
        }

        # Send POST request
        url = f"{api_server}/api/v2/compute/check-in"
        print(datetime.datetime.now(), url, data)
        response = requests.post(url,
                                 headers=headers,
                                 data=json.dumps(data),
                                 auth=HTTPBasicAuth(api_key, ''))

        if response.status_code == 200:
            response_data = response.json()
            # print(response_data)

            # Update vpn settings if changed
            if 'vpn_sha1' in response_data and 'vpn' in response_data and response_data[
                    'vpn_sha1'] != vpn_sha1:
                vpn_sha1 = response_data['vpn_sha1']
                vpn = response_data.get('vpn', vpn)
                with open('/cocalc/conf/vpn.json', 'w') as f:
                    json.dump(vpn, f, indent=2)

            # Update storage settings if changed
            if 'storage_sha1' in response_data and 'storage' in response_data and response_data[
                    'storage_sha1'] != storage_sha1:
                storage_sha1 = response_data['storage_sha1']
                storage = response_data.get('storage', storage)
                with open('/cocalc/conf/storage.json', 'w') as f:
                    json.dump(storage, f, indent=2)
        else:
            print(f"Error: Received status code {response.status_code}")
    except Exception as e:
        print(f"Exception during check-in: {str(e)}")


if __name__ == '__main__':
    if len(sys.argv) == 2:
        period_s = int(sys.argv[1])
    while True:
        check_in()
        time.sleep(period_s)
