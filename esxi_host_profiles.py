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
    if file.endswith(".xlsx") or file.endswith(".xls"):
        file_path = os.path.join(INPUT_FOLDER, file)

        df = pd.read_excel(file_path)

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
                "overall_status": get_overall_status(results),
                "results": results
            }

            grouped_hosts.append(host_data)

        # Output file name
        output_file = os.path.splitext(file)[0] + ".json"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(grouped_hosts, f, indent=4)

        print(f"Processed: {file} -> {output_file}")
