index=ssc_inspec_event_idx exec_mode=weekly_cis_host_profile bunit=host_profile
| spath
| table host_name overall_status platform hostprofiles ingestion_date

index=ssc_inspec_event_idx exec_mode=weekly_cis_host_profile bunit=host_profile
| spath
| mvexpand results{}
| spath input=results{}
| table host_name overall_status platform hostprofiles ingestion_date status incompliancedescription


index=ssc_inspec_event_idx exec_mode=weekly_cis_host_profile bunit=host_profile
| spath
| mvexpand results{}
| spath input=results{} output=status path=status
| spath input=results{} output=incompliancedescription path=incompliancedescription
| table host_name overall_status platform hostprofiles ingestion_date status incompliancedescription
---
def get_overall_status(results, hostprofiles):
    # Normalize hostprofiles (handle NaN / empty)
    if pd.isna(hostprofiles) or str(hostprofiles).strip() == "":
        hostprofiles_empty = True
    else:
        hostprofiles_empty = False

    has_no_profile = any(r["status"] == "no_profile_attached" for r in results)
    has_non_compliant = any(r["status"] == "non_compliant" for r in results)

    # New condition
    if hostprofiles_empty and has_no_profile:
        return "not_scanned"

    if has_non_compliant:
        return "non_compliant"

    return "compliant"

import os
import json
import pandas as pd
from datetime import datetime

# ================= CONSTANTS =================
BUNIT = "host_profile"
EXEC_MODE = "weekly_cis_host_profile"
PLATFORM = "esx_server"

INPUT_FOLDER = "input_folder_path"
OUTPUT_FOLDER = "output_folder_path"

# Create output folder if not exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Today's date
today_date = datetime.today().strftime('%Y-%m-%d')

# ===========================================

def normalize_status(value):
    if pd.isna(value):
        return "unknown"
    
    val = str(value).strip().lower()

    if "non" in val:
        return "non_compliant"
    elif "no profile" in val:
        return "no_profile_attached"
    else:
        return "compliant"


def get_overall_status(results):
    for r in results:
        if r["status"] == "non_compliant":
            return "non_compliant"
    return "compliant"


for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".csv"):
        file_path = os.path.join(INPUT_FOLDER, file)

        # Read CSV (handles encoding issues better)
        df = pd.read_csv(file_path, encoding="utf-8", engine="python")

        grouped_hosts = []

        # Group by VMHost
        for host, group in df.groupby("VMHost"):

            results = []

            for _, row in group.iterrows():
                status = normalize_status(row["Compliance"])

                results.append({
                    "status": status,
                    "incompliancedescription": row.get("IncomplianceDescription", "")
                })

            host_data = {
                "host_name": host,
                "version": group.iloc[0]["Version"],
                "build": group.iloc[0]["Build"],
                "hostprofiles": group.iloc[0]["HostProfile"],
                "ingestion_date": today_date,
                "platform": PLATFORM,
                "bunit": BUNIT,
                "exec_mode": EXEC_MODE,
                "overall_status": get_overall_status(results, group.iloc[0]["HostProfile"]),
                "results": results
            }

            grouped_hosts.append(host_data)

        # Output file name (same name, .json)
        output_file = os.path.splitext(file)[0] + ".json"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(grouped_hosts, f, indent=4)

        print(f"Processed: {file} -> {output_file}")
