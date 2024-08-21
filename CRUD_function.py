import pandas as pd
import streamlit as st
import zipfile
import os
from io import BytesIO
from dotenv import load_dotenv
import base64
import json
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

load_dotenv()

base64_encoded_service_account = st.secrets.BASE64_ENCODED_SERVICE_ACCOUNT
# Step 1: Decode the Base64-encoded string
decoded_service_account = base64.b64decode(base64_encoded_service_account).decode('utf-8')
# Step 2: Parse the decoded string as JSON
service_credentials = json.loads(decoded_service_account)


def login_with_service_account():
    """
    Google Drive service with a service account.
    note: for the service account to work, you need to share the folder or
    files with the service account email.

    :return: google auth
    """
    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    settings = {
                "client_config_backend": "service",
                "service_config": {
                    "client_json_dict": service_credentials,
                }
            }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth

drive = GoogleDrive(login_with_service_account())

def get_file_id_by_title(file_title):
    try:
        files = drive.ListFile({'q': f"title = '{file_title}'"}).GetList()
        return files[0]['id'] if files else None
    except Exception as e:
        print(f"Error retrieving file ID: {e}")
        return None

def get_folder_id_by_title(folder_title):
    try:
        folders = drive.ListFile({'q': f"title = '{folder_title}'"}).GetList()
        if folders and folders[0]['mimeType'] == 'application/vnd.google-apps.folder':
            return folders[0]['id']
        else:
            print(f"Folder '{folder_title}' not found or is not a folder.")
            return None
    except Exception as e:
        print(f"Error retrieving folder ID: {e}")
        return None

# level up above function
def upload(file_name, local_path, folder=None):
    try:
        file_id = get_file_id_by_title(file_name)
        folder_id = get_folder_id_by_title(folder) if folder else None
        
        if file_id:
            print('File found in Drive, updating file...')
            file_metadata = {'id': file_id}
            if folder_id:
                file_metadata['parents'] = [{"id": folder_id}]
                print(f"Folder '{folder}' detected.")
            update_file = drive.CreateFile(file_metadata)
        else:
            print('Uploading new file...')
            file_metadata = {'parents': [{"id": folder_id}]} if folder_id else {}
            if folder_id:
                print(f"Folder '{folder}' detected.")
            update_file = drive.CreateFile(file_metadata)

        update_file.SetContentFile(local_path)
        update_file.Upload()
        print('Done!')
        
    except Exception as e:
        print(f"Error during upload: {e}")

# function to read only
def read(file_name=None, folder=None):
    try:
        # Handle case when no folder is specified (root directory)
        if not folder:
            all_files = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
            df_all_files = pd.DataFrame({
                'ID': [f['id'] for f in all_files],
                'File Name': [f['title'] for f in all_files],
                'File Type': [f['mimeType'] for f in all_files]
            })
            return df_all_files
        
        # Handle case when a folder is specified
        folder_id = get_folder_id_by_title(folder)
        
        if not folder_id:
            print(f"Folder '{folder}' not found.")
            return None
        
        all_files_in_folder = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        df_all_files_in_folder = pd.DataFrame({
            'ID': [f['id'] for f in all_files_in_folder],
            'File Name': [f['title'] for f in all_files_in_folder],
            'File Type': [f['mimeType'] for f in all_files_in_folder]
        })
        
        return df_all_files_in_folder
    
    except Exception as e:
        print(f"Error during file operation: {e}")
        return None

def download_file(file_id, file_name, mime_type):
    try:
        # Retrieve the file from Google Drive
        file = drive.CreateFile({'id': file_id})
        file.GetContentFile(file_name, mimetype=mime_type)
        st.success(f"File '{file_name}' downloaded successfully.")
    except Exception as e:
        st.error(f"Error downloading file '{file_name}': {e}")


def zip_files(file_df):
    # Create a BytesIO object to hold the ZIP file in memory
    zip_buffer = BytesIO()

    # Create a ZIP file
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for index, file_info in file_df.iterrows():
            file_id = file_info['ID']
            file_name = file_info['File Name']
            mime_type = file_info['File Type']

            if mime_type == 'application/vnd.google-apps.spreadsheet':
                continue
            
                ##### THE CODE BELOW IS ONLY USED WITH OAUTH #####
                # url = f"https://docs.google.com/spreadsheets/export?id={file_id}&exportFormat=xlsx"
                # res = requests.get(url, headers={"Authorization": "Bearer " + login_with_service_account().attr['credentials'].access_token})
                # with open(f'{file_name}.xlsx', 'wb') as f:
                #     f.write(res.content)
                # zip_file.write(f'{file_name}.xlsx')
                # print(f'{file_name} berhasil masuk zip')
                # # Clean up the downloaded file
                # os.remove(f'{file_name}.xlsx')
                
            else:
                
                # Retrieve the file from Google Drive
                file = drive.CreateFile({'id': file_id})
                file.GetContentFile(file_name, mimetype = mime_type)
                zip_file.write(file_name)
                print(f'{file_name} berhasil masuk zip')
                # Clean up the downloaded file
                os.remove(file_name)
                
    # Set the position to the beginning of the BytesIO buffer
    zip_buffer.seek(0)

    return zip_buffer


def delete_FOREVER(file_name, folder=None):
    try:
        file_id = get_file_id_by_title(file_name)
        
        if not file_id:
            print(f"File '{file_name}' not found.")
            return
        
        folder_id = get_folder_id_by_title(folder) if folder else None
        
        if folder_id:
            print(f"Deleting '{file_name}' from folder '{folder}'...")
            file = drive.CreateFile({'id': file_id, 'parents': [{"id": folder_id}]})
        else:
            print(f"Deleting '{file_name}' from root or unspecified folder...")
            file = drive.CreateFile({'id': file_id})
        
        file.Trash()  # Move file to trash, permanently delete if necessary
        print(f"File '{file_name}' deleted successfully.")

    except Exception as e:
        st.write(f"Error during file deletion: {e}")