We implement a "Global Filesystem" (i.e., a "globalfs") using

- JuiceFS
- KeyDB
- Google Cloud Storage

This container does the following:

- It monitors the directory /data for a file storage.json, and when that file is created or changed, it updates its state.

- The format of storage.json is illustrated as follows:

```json
{
  "filesystems": [
    {
      "id": 1,
      "project_id": "16feb7be-328c-46f2-8e16-23c450f73f32",
      "account_id": "d8d23e45-83f5-4b67-a67f-2abb6707c4f2",
      "created": "2024-05-29T21:50:56.604Z",
      "bucket": "name-of-a-bucket",
      "mountpoint": "storage",
      "secret_key": {
        "type": "service_account",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "client_id": "...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "project_id": "cocal...",
        "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
        "client_email": "test-mounting-bucket@cocal....iam.gserviceaccount.com",
        "private_key_id": "79...e9",
        "universe_domain": "googleapis.com",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-mounting-bucket%40cocalccomputeservers-398318.iam.gserviceaccount.com",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
      },
      "port": 13100,
      "compression": "lz4" (or 'none' or 'zlib'),
      "configuration": {juice:{}, keydb:{}},
      "title": 'The Title',
      "color": '#abc',
      "deleted": false,
      "error": '',
      "notes": 'This is a demo.'
    },
    ...
  ],
  "network": {
    "interface": "10.11.223.213",
    "peers": [
      "10.11.64.181"
    ]
  }
}
```

- There are some changes that are not allowed.   E.g., the compression can't be changed after the filesystem is formatted.





