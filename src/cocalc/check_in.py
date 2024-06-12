#!/usr/bin/env python3
"""
- Periodically check in with cocalc saying that the server is alive.

- Response message may contain vpn and cloud filesystem; if so, we update them.


The check_in function below calls the remote API, similar to doing the following using curl from the command line

  curl -sk -u sk-eTUKbl2lkP9TgvFJ00001n: -d '{"id":"13","vpn_sha1":"fbdad59e0793e11ffa464834c647db93d1f9ec99","cloud_filesystem_sha1":"97d170e1550eee4afc0af065b78cda302a97674c"}' -H 'Content-Type: application/json' https://cocalc.com/api/v2/compute/check-in

However, instead of using curl, it uses the requests python library.

Here:
   - the api key like 'sk-eTUKbl2lkP9TgvFJ00001n' is in the file '/cocalc/conf/api_key'
   - cloud_filsystem_sha1 and vpn_sha1 are global variables defined above
   - the api server https://cocalc.com is in the file '/cocalc/conf/api_server'
   - the id is in the file /cocalc/conf/compute_server_id and shold be read from there.
   - the api_key and api_server and id will not change -- they only have to be read from the file once at script startup

The API response is json formatted has optional fields:
   - vpn
   - vpn_sha1
   - cloud_filsystem
   - cloud_filsystem_sha1
They should be used to update the above global variables whenever the sha1 changes.
Also, when vpn change, it should be written as valid json to the file /cocalc/conf/vpn.json,
and when cloud_filsystem changes, write it /cocalc/conf/cloud-filesystem.json.

"""
import datetime, json, os, sys, subprocess, time, requests
import argparse
import update_hosts
from requests.auth import HTTPBasicAuth

# by default, ping server every 30s. This parameter should
# be passed in as a command line arg.
DEFAULT_PERIOD = 30

# Check for watch path this often.
POLL_INTERVAL_S = 0.5

vpn_sha1 = ''
vpn = []
cloud_filesystem = []
cloud_filesystem_sha1 = ''
api_key = ''
api_server = ''
server_id = 0


def check_in():
    global vpn_sha1, vpn, cloud_filesystem_sha1, cloud_filesystem, api_key, api_server, server_id

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
            "cloud_filesystem_sha1": cloud_filesystem_sha1
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
                                 auth=HTTPBasicAuth(api_key, ''),
                                 timeout=10)

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

            # Update cloud_filesystem settings if changed
            if 'cloud_filesystem_sha1' in response_data and 'cloud_filesystem' in response_data and response_data[
                    'cloud_filesystem_sha1'] != cloud_filesystem_sha1:
                cloud_filesystem_sha1 = response_data['cloud_filesystem_sha1']
                cloud_filesystem = response_data.get('cloud_filesystem',
                                                     cloud_filesystem)
                with open('/cocalc/conf/cloud-filesystem.json', 'w') as f:
                    json.dump(cloud_filesystem, f, indent=2)
                    if isinstance(
                            cloud_filesystem, dict
                    ) and 'filesystems' in cloud_filesystem and len(
                            cloud_filesystem['filesystems']) > 0:
                        ensure_cloud_filesystem_container_is_running(
                            cloud_filesystem['image'])
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


launched_cloud_filesystem = 0


def ensure_cloud_filesystem_container_is_running(image):
    global launched_cloud_filesystem
    if time.time() - launched_cloud_filesystem < 60 * 10:
        # don't try again if we just started trying
        return
    s = subprocess.run(
        'docker ps --filter name=cloud-filesystem --format json'.split(),
        capture_output=True)
    if s.returncode:
        raise RuntimeError(s.stderr)
    if s.stdout.strip():
        # It is running already
        return
    launched_cloud_filesystem = time.time()
    print(
        "Start cloud filesystem container (could take a minute) in the background."
    )
    # Just in case docker container was left from previous startup, remove it, or can't create the one before.
    # The version could be different and its better to make a new one that start an existing one.
    os.system("docker rm cloud-filesystem || true")
    # We bind mount in /cocalc so nodejs is usable, and also the config is in /cocalc/conf.
    cmd = f"exec docker run -d --init --network host --name cloud-filesystem --privileged -v /cocalc:/cocalc --mount type=bind,source=/home/user,target=/home/user,bind-propagation=rshared {image} & "
    print(cmd)
    os.system(cmd)


def main(period_s=DEFAULT_PERIOD, watch_path=''):
    while True:
        try:
            print("Checking in...")
            t = time.time()
            check_in()
            wait_s = period_s - (time.time() - t)
            if wait_s <= 3:
                wait_s = 3
            elif wait_s >= period_s:
                wait_s = period_s
            print(f"Waiting {wait_s} seconds...")

            if not watch_path:
                time.sleep(wait_s)
            else:
                # wait wait_s or until watch_path exists.
                elapsed = 0
                while elapsed < wait_s:
                    time.sleep(POLL_INTERVAL_S)
                    elapsed += POLL_INTERVAL_S
                    if watch_path and os.path.exists(watch_path):
                        print(f"'{watch_path}' exists, so checking in")
                        os.remove(watch_path)
                        break

        except Exception as e:
            print("Error", e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Periodically check in with cocalc.')
    parser.add_argument('period',
                        type=int,
                        nargs='?',
                        default=DEFAULT_PERIOD,
                        help='Check-in period in seconds')
    parser.add_argument(
        'watch_path',
        type=str,
        nargs='?',
        default='',
        help=
        'Path to a file to watch for creation. Delete file and check-in immediately if the file is created. This makes it possible to cause an immediate check-in, e.g., when mounting a filesystem or updating ssh keys or the vpn.'
    )
    args = parser.parse_args()

    period_s = args.period
    watch_path = args.watch_path
    main(period_s, watch_path)
