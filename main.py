import streamlit as st
import pandas as pd
from io import BytesIO
from CRUD_function import upload, read, delete_FOREVER, zip_files

# Streamlit App
st.title("Google Drive File Manager")

# Choose an operation
operation = st.sidebar.selectbox(
    "Choose an operation",
    ("Upload File", "Read Files", "Download File", "Delete File")
)

# Upload File
if operation == "Upload File":
    st.header("Upload File to Google Drive")

    file = st.file_uploader("Choose a file", accept_multiple_files=True)
    folder = st.text_input("Folder Name (leave blank for root)")

    if st.button("Upload/Update"):
        if file:
            for file_to_upload in file:
                with open(file_to_upload.name, "wb") as f:
                    f.write(file_to_upload.getbuffer())
                upload(file_to_upload.name, file_to_upload.name, folder)
                st.success(f"'{file_to_upload.name}' uploaded successfully to '{folder or 'root'}'.")

# Read Files
if operation == "Read Files":
    st.header("Read Files from Google Drive")

    folder = st.text_input("Folder Name (leave blank for root)")

    if st.button("Read Files"):
        if folder:
            files_df = read(folder=folder)
        else:
            files_df = read()

        if files_df is not None:
            st.write(files_df)
            
            # Download the DataFrame as Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                files_df.to_excel(writer, index=False)
            output.seek(0)
            st.download_button(
                label="Download Excel",
                data=output,
                file_name="google_drive_files.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.warning("No files found.")

# Download File
if operation == "Download File":
    st.header("Download Files from Google Drive")

    folder = st.text_input("Folder Name (leave blank for root)")

    if st.button("Read Files to Download"):
        if folder:
            files_df = read(folder=folder)
        else:
            files_df = read()

        if files_df is not None:
            st.write(files_df)
            
            # Download files as ZIP
            with st.spinner(f"Zipping {len(files_df)} files..."):
                zip_buffer = zip_files(file_df=files_df)
                
            st.download_button(
                label="Download ZIP",
                data=zip_buffer,
                file_name="google_drive_files.zip",
                mime="application/zip"
            )
            st.success("Files Ready to Download!")

# Delete File
elif operation == "Delete File":
    st.header("Delete File from Google Drive")

    file_name = st.text_input("File Name")
    folder = st.text_input("Folder Name (leave blank for root)")

    if st.button("Delete"):
        delete_FOREVER(file_name, folder)
        # st.success(f"'{file_name}' deleted successfully from '{folder or 'root'}'.")

