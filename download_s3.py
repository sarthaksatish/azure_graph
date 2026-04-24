import boto3
import os
from urllib.parse import urlparse

def download_s3_folder(s3_path, local_dir):
    parsed = urlparse(s3_path)
    bucket_name = parsed.netloc
    prefix = parsed.path.lstrip('/')

    s3 = boto3.client('s3')

    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if 'Contents' not in page:
            continue

        for obj in page['Contents']:
            key = obj['Key']

            # Skip "folder" placeholders
            if key.endswith('/'):
                continue

            # Create local file path
            relative_path = os.path.relpath(key, prefix)
            local_file_path = os.path.join(local_dir, relative_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Download file
            print(f"Downloading {key} -> {local_file_path}")
            s3.download_file(bucket_name, key, local_file_path)

    print("Download complete.")
