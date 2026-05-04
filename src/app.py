import streamlit as st
import json
import sys
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from chromadb.utils import embedding_functions

CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_chat_history(messages):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(messages, f)

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.components.sidebar import render_sidebar
from src.utils.llm_service import generate_answer
from src.utils.vectorstore import VectorStore

@st.cache_resource
def initialize_embedding_model():
    return embedding_functions.DefaultEmbeddingFunction()

def recursive_split(text, chunk_size=800, overlap=150):
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split(text, sep_index=0):
        if len(text) <= chunk_size or sep_index >= len(separators):
            return [text]
        
        sep = separators[sep_index]
        parts = text.split(sep) if sep else list(text)
        
        chunks = []
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > chunk_size:
                    chunks.extend(split(part, sep_index + 1))
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)
        return chunks
    
    raw_chunks = split(text)
    final = []
    for i, chunk in enumerate(raw_chunks):
        if i == 0:
            final.append(chunk)
        else:
            # Add context from the end of the previous chunk
            overlap_text = raw_chunks[i-1][-overlap:]
            final.append(overlap_text + chunk)
    return final

def chunk_text_with_metadata(pdf_reader, filename, chunk_size=800, overlap=150):
    chunks = []
    metadatas = []
    
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if not text: continue
        
        # Using the recursive logic instead of the while loop
        page_chunks = recursive_split(text, chunk_size=chunk_size, overlap=overlap)
        for chunk in page_chunks:
            chunks.append(chunk)
            metadatas.append({"source": filename, "page": page_num + 1})
            
    return chunks, metadatas

def main():
    st.set_page_config(page_title="RAG App", page_icon="🤖", layout="wide")
    st.title("📚 Universal RAG Assistant")
    
    with st.spinner("Initializing Local Vector Database..."):
        initialize_embedding_model()
        
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = VectorStore()
        # Retrieve already processed files from the persistent database
        existing_docs = st.session_state.vector_store.collection.get()
        if existing_docs and existing_docs['metadatas']:
            st.session_state.processed_files = set([meta['source'] for meta in existing_docs['metadatas']])
        else:
            st.session_state.processed_files = set()
            
    if "messages" not in st.session_state:
        st.session_state.messages = []

    render_sidebar()

    # --- NEW: UI Document Filter ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Target Search")

    # Initialize chat history from the file, not just an empty list
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Create a multiselect box populated with all indexed files
    selected_docs = st.sidebar.multiselect(
        "Search within specific documents:",
        options=list(st.session_state.processed_files),
        default=list(st.session_state.processed_files) # Default to searching everything
    )
    
    with st.expander("📁 Add Knowledge Base (PDFs)", expanded=not st.session_state.processed_files):
        # Show what is currently in the persistent database
        if st.session_state.processed_files:
            st.markdown("**Currently Indexed Files:**")
            for f in st.session_state.processed_files:
                st.markdown(f"- `{f}`")
                
        uploaded_files = st.file_uploader("Upload PDFs to converse with them", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.processed_files:
                    with st.spinner(f"Processing & Embedding {uploaded_file.name}..."):
                        try:
                            pdf_reader = PdfReader(uploaded_file)
                            # Get text and metadata
                            chunks, metadatas = chunk_text_with_metadata(pdf_reader, uploaded_file.name)
                            
                            # Add to persistent database
                            st.session_state.vector_store.add_documents(chunks, metadatas)
                            st.session_state.processed_files.add(uploaded_file.name)
                            
                            st.success(f"Successfully Indexed: {uploaded_file.name}")
                            st.rerun() # Refresh to show new files in the UI
                        except Exception as e:
                            st.error(f"Error reading {uploaded_file.name}: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your documents..."):
        if not st.session_state.api_key:
            st.error("Please enter your API Key in the sidebar.")
            return
        if not st.session_state.processed_files:
            st.warning("Please upload a document first.")
            return

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            
            # 1. Rewrite the Query based on Chat History
            with st.spinner("Contextualizing query..."):
                standalone_query = rewrite_query_with_context(
                    api_key=st.session_state.api_key,
                    provider=st.session_state.provider,
                    model_name=st.session_state.model_name,
                    chat_history=st.session_state.messages,
                    current_query=prompt
                )
                
            # 2. Search using the REWRITTEN query
            with st.spinner(f"Searching documents for: '{standalone_query}'..."):
                relevant_docs, relevant_metadatas = st.session_state.vector_store.similarity_search(
                    standalone_query, # Use the new standalone query!
                    allowed_sources=selected_docs 
                )
                
            # 3. Generate the final answer
            with st.spinner(f"Thinking via {st.session_state.provider.capitalize()}..."):
                answer = generate_answer(
                    api_key=st.session_state.api_key,
                    provider=st.session_state.provider,
                    model_name=st.session_state.model_name,
                    documents=relevant_docs,
                    metadatas=relevant_metadatas,
                    chat_history=st.session_state.messages,
                    current_query=prompt # We still pass the original prompt to the final generator
                )
            st.markdown(answer)
            
            # UPGRADE: Expanded view now shows the exact page numbers used
            with st.expander("🔍 View Retrieved Sources"):
                for i, (doc, meta) in enumerate(zip(relevant_docs, relevant_metadatas)):
                    st.markdown(f"**Source {i+1}:** `{meta['source']}` (Page {meta['page']})")
                    st.caption(f'"{doc.strip()}"')
                    st.markdown("---")

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Save the updated history to the file!
        save_chat_history(st.session_state.messages)

if __name__ == "__main__":
    main()