#!/usr/bin/env python3
"""
This is like "docker pull image[:tag]", except that it doesn't do
anything if the latest version is available locally, and if the
latest verstion is not available locallly, it first deletes
the local version of the image before doing the pull, in order
to avoid wasting disk space.
"""

import json, subprocess, sys


def get_digest(image, tag):
    cmd = ['docker', 'manifest', 'inspect', f"{image}:{tag}", "-v"]
    output = json.loads(subprocess.check_output(cmd).decode().strip())
    # note in case of multiarch, output will be an array of entries
    # for each arch. We do not need or support that here!
    return output['Descriptor']['digest']


def local_digests(image):
    cmd = [
        'docker', 'images', f'--filter=reference={image}', '--digests',
        '--format', '{{.ID}} {{.Digest}}'
    ]
    output = subprocess.check_output(cmd).decode().strip().splitlines()
    # map from digest to id
    digests = {}
    for x in output:
        v = x.split()
        digests[v[1]] = v[0]
    return digests


def delete_if_possible(ids):
    if len(ids) == 0:
        return
    try:
        subprocess.check_output(['docker', 'image', 'rm'] + list(ids))
    except Exception as e:
        print("WARNING: issue deleting", ids)
        print("Exception:", e)


def pull(image, tag):
    print(f"pull {image}:{tag}")
    local = local_digests(image)
    if len(local) > 0:
        desired = get_digest(image, tag)
        if desired in local:
            if len(local) > 1:
                print(
                    f"delete {len(local) - 1} older local image to save space")
                v = []
                for digest in local:
                    if digest != desired:
                        v.append(local[digest])
                delete_if_possible(v)
            return
        if len(local) > 0:
            # attempt to delete all the local ones
            print(f"delete the {len(local)} local image before pulling")
            delete_if_possible(local.values())
    # *then* pull the desired one
    print(f"pulling {image}:{tag}")
    subprocess.check_output(['docker', 'pull', f"{image}:{tag}"])


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f"Usage: {sys.argv[0]} image [tag]")
        print(
            "Does 'docker pull image:tag' but deleting any local older versions of image first."
        )
        sys.exit(1)
    v = sys.argv[1].split(':')
    image = v[0]
    if len(v) > 1:
        tag = v[1]
    else:
        tag = 'latest'
    pull(image, tag)
