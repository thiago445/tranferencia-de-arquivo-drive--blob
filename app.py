# pip install streamlit google-api-python-client google-auth azure-storage-blob

import io
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from azure.storage.blob import BlobServiceClient

# ── Config ────────────────────────────────────────────────────────────────────
AZURE_CONN_STR = (
    "BlobEndpoint=https://stodsm6p2.blob.core.windows.net/;"
    "QueueEndpoint=https://stodsm6p2.queue.core.windows.net/;"
    "FileEndpoint=https://stodsm6p2.file.core.windows.net/;"
    "TableEndpoint=https://stodsm6p2.table.core.windows.net/;"
    "SharedAccessSignature=sv=2026-02-06&ss=b&srt=sco&sp=rwdlaciytfx"
    "&se=2026-06-08T20:41:40Z&st=2026-05-25T12:26:40Z&spr=https,http"
    "&sig=4ZaFti31frOhQfvDnNOlFPaad%2FgAjEeDiiGS8AlxJfU%3D"
)
AZURE_CONTAINER = "aluno-thiago"
GDRIVE_CREDS    = "credentials.json"
SCOPES          = ["https://www.googleapis.com/auth/drive.readonly"]

# ── Clients ───────────────────────────────────────────────────────────────────
@st.cache_resource
def gdrive():
    creds = service_account.Credentials.from_service_account_file(GDRIVE_CREDS, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

@st.cache_resource
def azure():
    return BlobServiceClient.from_connection_string(AZURE_CONN_STR)

# ── Functions ─────────────────────────────────────────────────────────────────
def list_drive(folder_id="root"):
    q = f"'{folder_id}' in parents and trashed=false"
    res = gdrive().files().list(q=q, fields="files(id,name,mimeType,size)").execute()
    return res.get("files", [])

def get_or_create_container():
    # Cria o cliente do Azure
    blob_service_client = azure()
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER)
    
    # Verifica se o contêiner existe. Se não existir, cria na hora!
    if not container_client.exists():
        blob_service_client.create_container(AZURE_CONTAINER)
        
    return container_client

def list_blobs():
    cc = get_or_create_container()
    return [b.name for b in cc.list_blobs()]

def migrate(files, log):
    svc = gdrive()
    cc  = get_or_create_container()
    
    for f in files:
        name = f["name"]
        try:
            buf = io.BytesIO()
            req = svc.files().get_media(fileId=f["id"])
            dl  = MediaIoBaseDownload(buf, req)
            done = False
            while not done:
                _, done = dl.next_chunk()
            buf.seek(0)
            cc.upload_blob(name, buf, overwrite=True)
            msg = f"✅ {name}"
            print(msg)
        except Exception as e:
            msg = f"❌ {name} — {e}"
            print(msg)
        log.markdown(f"`{msg}`")

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Drive → Azure", page_icon="☁️", layout="wide")
st.title("☁️ Google Drive → Azure Blob Storage")

folder_id = st.text_input("Google Drive Folder ID (deixe vazio para raiz)", value="root")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📂 Listar Drive"):
        with st.spinner("Buscando arquivos..."):
            files = list_drive(folder_id)
        st.success(f"{len(files)} arquivo(s) encontrado(s)")
        st.dataframe(
            [{"Nome": f["name"], "Tipo": f["mimeType"], "Tamanho": f.get("size", "—")} for f in files],
            use_container_width=True,
        )

with col2:
    if st.button("🗂️ Listar Azure"):
        with st.spinner("Buscando blobs..."):
            blobs = list_blobs()
        st.success(f"{len(blobs)} blob(s) encontrado(s)")
        st.dataframe({"Blob": blobs}, use_container_width=True)

with col3:
    if st.button("🚀 Migrar Arquivos", type="primary"):
        with st.spinner("Migrando..."):
            files = list_drive(folder_id)
        if not files:
            st.warning("Nenhum arquivo encontrado no Drive.")
        else:
            st.info(f"Migrando {len(files)} arquivo(s)...")
            log = st.empty()
            migrate(files, log)
            st.success("Migração concluída!")