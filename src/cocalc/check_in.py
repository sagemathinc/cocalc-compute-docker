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
import datetime, json, os, sys, subprocess, time, requests
import update_hosts
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
                update_vpn()

            # Update storage settings if changed
            if 'storage_sha1' in response_data and 'storage' in response_data and response_data[
                    'storage_sha1'] != storage_sha1:
                storage_sha1 = response_data['storage_sha1']
                storage = response_data.get('storage', storage)
                with open('/cocalc/conf/storage.json', 'w') as f:
                    json.dump(storage, f, indent=2)
                    if isinstance(storage,
                                  dict) and 'filesystems' in storage and len(
                                      storage['filesystems']) > 0:
                        ensure_storage_container_is_running(storage['image'])
        else:
            print(f"Error: Received status code {response.status_code}")
    except Exception as e:
        print(f"Exception during check-in: {str(e)}")


def run(cmd):
    print(f"Run '{cmd}'")
    os.system(cmd)


def update_vpn():
    image = json.loads(open('/cocalc/conf/vpn.json').read())['image']
    # Process latest vpn configuration
    run(f'docker run --rm --network host --privileged -v /cocalc/conf:/cocalc/conf {image}'
        )
    # Update /etc/hosts on the root VM
    update_hosts.update_hosts()
    # Update /etc/hosts in the compute docker container
    run('docker exec compute sudo /cocalc/update_hosts.py')
    # NOTE: you can't just bind mount /etc/hosts into the container, and you can't just edit /etc/hosts
    # from a bind mounted /etc in a container -- i.e., every approach to *directly* using /etc/hosts
    # that I tried failed, and should fail (as it would lead to subtle bugs).  Being explicit with the update_hosts.py
    # command is much better.
    if os.path.exists('/cocalc/conf/pings.sh'):
        # launch pings in the background to keep us on the vpn from behind our firewall.
        os.system("exec /cocalc/conf/pings.sh &")


launched_storage = 0


def ensure_storage_container_is_running(image):
    global launched_storage
    if time.time() - launched_storage < 60 * 10:
        # don't try again if we just started trying
        return
    s = subprocess.run('docker ps --filter name=storage --format json'.split(),
                       capture_output=True)
    if s.returncode:
        raise Error(s.stderr)
    if s.stdout.strip():
        # It is running already
        return
    launched_storage = time.time()
    print(
        "Start storage container (could take a minute), so do it in the background."
    )
    # Just in case docker container was left from previous startup, remove it, or can't create the one before.
    # The version could be different and its better to make a new one that start an existing one.
    os.system("docker rm storage || true")
    cmd = f"exec docker run -d --init --network host --name storage --privileged -v /cocalc/conf:/cocalc/conf --mount type=bind,source=/home/user,target=/home/user,bind-propagation=rshared {image} & "
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        period_s = int(sys.argv[1])
    while True:
        try:
            t = time.time()
            check_in()
            wait_s = period_s - (time.time() - t)
            if wait_s <= 0:
                wait_s = 0
            elif wait_s >= 60 * 5:
                wait_s = 60 * 5
            print(f"Waiting {wait_s} seconds...")
            time.sleep(wait_s)
        except Exception as e:
            print(f"Error -- '{cmd}'")
            pass
