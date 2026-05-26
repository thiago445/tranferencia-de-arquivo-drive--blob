# pip install streamlit azure-storage-blob

import streamlit as st
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

# ── Clients ───────────────────────────────────────────────────────────────────
@st.cache_resource
def azure():
    return BlobServiceClient.from_connection_string(AZURE_CONN_STR)

# ── Functions ─────────────────────────────────────────────────────────────────
def get_or_create_container():
    blob_service_client = azure()
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER)
    
    # Cria o contêiner automaticamente se não existir
    if not container_client.exists():
        blob_service_client.create_container(AZURE_CONTAINER)
        
    return container_client

def list_blobs():
    cc = get_or_create_container()
    return [b.name for b in cc.list_blobs()]

def upload_files(files, log):
    cc = get_or_create_container()
    for f in files:
        name = f.name
        try:
            cc.upload_blob(name, f, overwrite=True)
            msg = f"✅ {name}"
            print(msg)
        except Exception as e:
            msg = f"❌ Erro em {name} — {e}"
            print(msg)
        log.markdown(f"`{msg}`")

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Upload Local → Azure", page_icon="☁️", layout="wide")
st.title("☁️ Upload Local → Azure Blob Storage")
st.write("Selecione os arquivos do seu computador para enviá-los diretamente para o contêiner da Azure.")

# Área para o usuário fazer upload dos arquivos do próprio computador
uploaded_files = st.file_uploader("📂 Escolha os arquivos de origem", accept_multiple_files=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("🗂️ Listar Destino (Azure)"):
        with st.spinner("Buscando blobs..."):
            blobs = list_blobs()
        st.success(f"{len(blobs)} arquivo(s) encontrado(s) no Azure")
        st.dataframe({"Arquivos na Nuvem": blobs}, use_container_width=True)

with col2:
    if st.button("🚀 Enviar Arquivos para Azure", type="primary"):
        if not uploaded_files:
            st.warning("Por favor, selecione pelo menos um arquivo na área acima primeiro.")
        else:
            st.info(f"Enviando {len(uploaded_files)} arquivo(s)...")
            log = st.empty()
            upload_files(uploaded_files, log)
            st.success("Transferência concluída!")