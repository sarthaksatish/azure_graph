my platform values which are appearing in json are RHEL, Windows2019, Windows2022, amazon 2023.10.20260216, amazon 2023.10.20260302, redhat 9.6, redhat 9.7, windows_server_2022_datacenter 10.0.20348, amazon 2, amazon 2023.7.20250414, amazon 2023.9.20250414, amazon 2023.9.20250014, amazon 2023.9.2025027, amazon_linux_2023, amazon_linux_2, redhat_redhat_enterprise_linux_8.10 i have kept my waiver file according to business unit - awscentral: - platform: "amazon 2023" waivers_id: - 1.1.3.1 - platform: "amazon 2" waivers_id: - 1.1.3.1 - platform: "redhat 8" waivers_id: - 1.1.3.1 - crdpm: - platform: "windows 2022" waivers_id: - 1.1.3.1 - platform: "amazon 2023" waivers_id: - 1.1.3.1 - platform: "redhat 8" waivers_id: - 1.1.3.1 - platform: "redhat 9" waivers_id: - 1.1.3.1 - ssc_azure: - platform: "windows 2022" waivers_id: - 1.1.3.1 - platform: "windows 2019" waivers_id: - 1.1.3.1 - platform: "redhat 8" waivers_id: - 1.1.3.1 for waiver_key, ids in waiver_map.items(): # split waiver key into parts (e.g. "windows 2022" -> ["windows", "2022"]) key_parts = waiver_key.lower().split() # check if all parts exist in platform string if all(part in platform for part in key_parts): if check_id in ids: if item.get("status") != "skipped": item["status"] = "skipped" modified = True i need a way to match these platforms and apply waivers i dont want to match exact string for each platform it will be lengthy waivers code which is not good please take care of case sensitive, when platform comes as RHEL it should check in respective business unit if redhat 8 or redhat 9 is there and apply those waiviers

import re

def normalize_platform(platform: str) -> str:
    p = platform.lower()

    # --- WINDOWS ---
    if "windows" in p:
        if "2019" in p:
            return "windows 2019"
        if "2022" in p:
            return "windows 2022"

    # --- AMAZON ---
    if "amazon" in p:
        if "2023" in p:
            return "amazon 2023"
        if re.search(r"\b2\b", p):
            return "amazon 2"

    # --- REDHAT ---
    if "redhat" in p:
        if "8" in p:
            return "redhat 8"
        if "9" in p:
            return "redhat 9"

    # --- RHEL (no version) ---
    if "rhel" in p:
        return "redhat"   # generic fallback

    return None

normalized = normalize_platform(platform)

for waiver_key, ids in waiver_map.items():
    waiver_key = waiver_key.lower()

    match = False

    # Exact match (normal case)
    if normalized == waiver_key:
        match = True

    # Special case: RHEL → match all redhat versions
    elif normalized == "redhat" and waiver_key.startswith("redhat"):
        match = True

    if match and check_id in ids:
        if item.get("status") != "skipped":
            item["status"] = "skipped"
            modified = True



----
for waiver_key, ids in waiver_map.items():
            # split waiver key into parts (e.g. "windows 2022" -> ["windows", "2022"])
            key_parts = waiver_key.lower().split()

            # check if all parts exist in platform string
            if all(part in platform for part in key_parts):
                if check_id in ids:
                    if item.get("status") != "skipped":
                        item["status"] = "skipped"
                        modified = True
---
import os
import json
import boto3
import re
from datetime import datetime
from botocore.config import Config

proxies = {
    "https": "http://your.proxy.server:8080"  # Replace if needed
}

def get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("access_key"),
        aws_secret_access_key=os.getenv("secret_key"),
        region_name=os.getenv("AWS_REGION", "us-west-2"),
        config=Config(proxies=proxies)
    )

def get_all_json_keys(bucket, prefix, s3):
    """Recursively list all JSON files under a prefix."""
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json"):
                yield key


def process_json_object(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)

    # Extract platform info safely
    platform_name = data.get("platform", {}).get("name", "")
    platform_release = data.get("platform", {}).get("release", "")
    platform = f"{platform_name} {platform_release}".strip()

    parts = key.split("/")

    ingestion_date = datetime.utcnow().strftime("%Y-%m-%d")
    date = parts[2]
    region = parts[3]
    environment = parts[4]
    instance_file = parts[5]

    base_name = instance_file.rsplit(".json", 1)[0]

    m = re.search(r"-\d{4}-\d{2}-\d{2}-T", base_name)
    if m:
        instance_name = base_name[:m.start()]
    else:
        instance_name = base_name

    host_name = f"Name@{instance_name}"

    output = []

    profiles = data.get("profiles", [])
    for profile in profiles:
        for control in profile.get("controls", []):
            title = control.get("title", "")
            description = control.get("desc", "")
            control_results = control.get("results", [])

            # 🔹 Determine overall control status
            overall_status = "passed"
            for r in control_results:
                if r.get("status", "").lower() == "failed":
                    overall_status = "failed"
                    break

          

                filtered_results = []
                letters = string.ascii_lowercase
                
                for idx, r in enumerate(control_results[:26]):  # 🔹 limit to 26 items
                    suffix = letters[idx]
                    filtered_results.append({
                        "id": f"{cis_id}{suffix}"
                    })

            output.append({
                "host_name": host_name,
                "title": title,
                "description": description,
                "status": overall_status,
                "code_desc": None,  # optional, since we are keeping full results
                "platform": platform,
                "environment": environment,
                "region": region,
                "ingestion_date": ingestion_date,
                "results": control_results,  # ✅ keep original results array
                "bunit": "crdpm"
            })

    return output



def main():
    s3 = get_client()

    bucket = "prod-db-backup-daily"
    prefix = "CIS-Scans/weekly-reports/2026-02-10/"

    final_output = []

    print("Scanning S3 path...")
    for key in get_all_json_keys(bucket, prefix, s3):
        print(f"Processing: {key}")
        records = process_json_object(s3, bucket, key)
        final_output.extend(records)

    with open("aggregated_output.json", "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n✅ Done. Total flattened records: {len(final_output)}")


if __name__ == "__main__":
    main()
