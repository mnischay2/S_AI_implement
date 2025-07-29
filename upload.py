import os
import requests

# === Configuration ===
API_URL = "http://bodh_uat.sarthhakai.com/utilitiesservice/upload-files/Documents"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjMGJmMGQ0OC04MWY2LTRmYjctYWMwOS02MjU2NjNhYjBlOTIiLCJ0SWQiOiI2YmE2NzA3NC0wNjE1LTQ4OWMtYmMwYy03OTEwYjA0MDYzYzIiLCJvcmdJZCI6ImUxNjhlMWU1LTEyMzEtNGE4ZC1hYmNmLWQ2NmM3NDU1MjIyOCIsImZpcnN0TmFtZSI6IklJUEQiLCJsYXN0TmFtZSI6ImJvZGhpIiwicm9sZSI6IlVTRVIiLCJzdWJzY3JpcHRpb25fcXVhbnRpdHkiOjgsImlhdCI6MTc1MjgzNjIzNiwiZXhwIjo0OTA4NTk2MjM2fQ.rce5Ayeaslhv5ZcjUX5mEc9MbgaVQzAhyOhn_reFDc0"  # Replace with your valid bearer token
CSV_FOLDER = "csv_data"

def upload_csv_file(filepath, filename, api_url, auth_token):
    """Uploads a single CSV file to the given API."""
    try:
        with open(filepath, 'rb') as file:
            files = {'files': (filename, file, 'text/csv')}
            headers = {'Authorization': f'Bearer {auth_token}'}
            response = requests.post(api_url, files=files, headers=headers)

        if response.status_code == 200:
            print(f"✅ Uploaded: {filename}")
            os.remove(filepath)
            return True
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error uploading {filename}: {e}")
        return False

def upload_all_csv(folder_path=CSV_FOLDER, api_url=API_URL, auth_token=AUTH_TOKEN):
    """Uploads all CSV files in the specified folder."""
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    if not csv_files:
        print("ℹ️ No CSV files to upload.")
        return

    for filename in csv_files:
        filepath = os.path.join(folder_path, filename)
        upload_csv_file(filepath, filename, api_url, auth_token)
    return("done")

if __name__ == "__main__":
    print(upload_all_csv())
