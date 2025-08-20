import os
import requests
import csv

# === Configuration ===
API_URL = "http://bodh_uat.sarthhakai.com/utilitiesservice/upload-files/documents"
create_URL = "http://bodh_uat.sarthhakai.com/userservice/createDocument"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjMGJmMGQ0OC04MWY2LTRmYjctYWMwOS02MjU2NjNhYjBlOTIiLCJ0SWQiOiI2YmE2NzA3NC0wNjE1LTQ4OWMtYmMwYy03OTEwYjA0MDYzYzIiLCJvcmdJZCI6ImUxNjhlMWU1LTEyMzEtNGE4ZC1hYmNmLWQ2NmM3NDU1MjIyOCIsImZpcnN0TmFtZSI6IklJUEQiLCJsYXN0TmFtZSI6ImJvZGhpIiwicm9sZSI6IlVTRVIiLCJzdWJzY3JpcHRpb25fcXVhbnRpdHkiOjgsImlhdCI6MTc1MjgzNjIzNiwiZXhwIjo0OTA4NTk2MjM2fQ.rce5Ayeaslhv5ZcjUX5mEc9MbgaVQzAhyOhn_reFDc0"  # Replace with your valid bearer token
CSV_FOLDER = "csv_data"

def upload_csv(filename):
    """Uploads a single CSV file to the given API."""
    filepath = os.path.join(CSV_FOLDER, filename)
    try:
        with open(filepath, 'r', newline='') as f_check:
            reader = csv.reader(f_check)
            rows = list(reader)
            if len(rows) <= 1:
                print(f"⚠️ Skipped (no data): {filename}")
                return "⚠️ Cannot upload as there's no data in the file."
            
        with open(filepath, 'rb') as file:
            files = {'files': (filename, file, 'text/csv')}
            headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
            response = requests.post(API_URL, files=files, headers=headers)
    
        if response.status_code == 200:
            print(f"✅ Uploaded: {filename}")
            os.remove(filepath)
            print(response.text)
            return("done")
        
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code} - {response.text}")
            return (f"❌ Failed to upload {filename}: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error uploading {filename}: {e}")
        return (f"❌ Error uploading {filename}: {e}")

def upload_all_csv():
    """Uploads all CSV files in the specified folder."""
    if not os.path.exists(CSV_FOLDER):
        print(f"⚠️ Folder not found: {CSV_FOLDER}")
        return

    csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
    if not csv_files:
        print("ℹ️ No CSV files to upload.")
        return ("no csv files found")

    for filename in csv_files:
        filepath = os.path.join(CSV_FOLDER, filename)
        upload_csv(filename)
    return("done")

if __name__ == "__main__":
    print(upload_all_csv())
