import streamlit as st
import time
import urllib.parse
import requests
import zipfile
import os
import tempfile
import random
from zeroentropy import ZeroEntropy

PREDEFINED_CORPORA = {
    "maud": {
        "name": "MAUD",
        "description": "MAUD: Merger Agreement Understanding Dataset",
        "corups_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/ALwI_ohLY7KCg7veDdHdAb8/corpus/maud?dl=0&rlkey=5n8zrbk4c08lbit3iiexofmwg&subfolder_nav_tracking=1&dl=1",
        "queries_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/APO2GVe0eOLUG5Hm9Rdoa5Q/benchmarks/maud.json?rlkey=5n8zrbk4c08lbit3iiexofmwg&dl=1",
    },
    "contractnli": {
        "name": "ContractNLI",
        "description": "ContractNLI: Legal Contract Natural Language Inference Dataset",
        "corups_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/AA-MC5kfSSovBb6zOzlIEt8/corpus/contractnli?rlkey=5n8zrbk4c08lbit3iiexofmwg&subfolder_nav_tracking=1&st=fm5o1owj&dl=1",
        "queries_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/APhiRxuoZvoq8sbUAJp_9IE/benchmarks/contractnli.json?rlkey=5n8zrbk4c08lbit3iiexofmwg&dl=1",
    },
    "cuad": {
        "name": "CUAD",
        "description": "CUAD: Contract Understanding Atticus Dataset",
        "corups_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/AL0guPQHmsmOjJerxZDEk_4/corpus/cuad?dl=0&rlkey=5n8zrbk4c08lbit3iiexofmwg&subfolder_nav_tracking=1&dl=1",
        "queries_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/AOokCanBJ5IHk5TEMP699YE/benchmarks/cuad.json?rlkey=5n8zrbk4c08lbit3iiexofmwg&dl=1",
    },
    "privacy_qa": {
        "name": "PrivacyQA",
        "description": "PrivacyQA: Question Answering for Privacy Policies",
        "corups_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/AH_DYzwpq8JDseRV3ZJq6Eo/corpus/privacy_qa?dl=0&rlkey=5n8zrbk4c08lbit3iiexofmwg&subfolder_nav_tracking=1&dl=1",
        "queries_url": "https://www.dropbox.com/scl/fo/r7xfa5i3hdsbxex1w6amw/ALHLEScOciSetNpW89rS79o/benchmarks/privacy_qa.json?rlkey=5n8zrbk4c08lbit3iiexofmwg&dl=1",
    },
}


def fetch_existing_collections(client: ZeroEntropy) -> list[str]:
    """Fetch existing collections using proper API calls"""
    response = client.collections.get_list()
    return response.collection_names


def create_or_get_collection(
    client: ZeroEntropy, collection_name: str
) -> tuple[bool, str]:
    """Try to create a collection, or just use it if it already exists"""
    try:
        client.collections.add(collection_name=collection_name)
        return True, f"✅ Created new collection: {collection_name}"
    except Exception as e:
        if "409" in str(e) or "already exists" in str(e).lower():
            return True, f"✅ Using existing collection: {collection_name}"
        else:
            return False, f"❌ Failed to create/access collection: {e}"


def download_corpus(url: str, temp_dir: str, corpus_name: str) -> list[dict]:
    """Download and extract corpus from URL"""
    response = requests.get(url)
    response.raise_for_status()

    zip_path = os.path.join(temp_dir, "corpus.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)

    documents = []
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith((".txt", ".json")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if content.strip():
                                documents.append(
                                    {
                                        "id": f"{corpus_name}_{file.replace('.txt', '').replace('.json', '')}",
                                        "content": content,
                                        "filename": file,
                                        "corpus_name": corpus_name,
                                        "original_path": file,
                                    }
                                )
                    except Exception as e:
                        st.warning(f"Could not read {file}: {e}")

    return documents


def download_queries(queries_url: str) -> dict:
    """Download and parse queries JSON from URL"""
    try:
        response = requests.get(queries_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to download queries: {e}")
        return {}


def check_corpus_indexed(
    client: ZeroEntropy, collection_name: str, corpus_name: str
) -> tuple[bool, int, int]:
    """Check if corpus documents are indexed in the collection"""
    try:
        doc_list = client.documents.get_info_list(
            collection_name=collection_name, path_prefix=f"{corpus_name}_"
        )

        total_docs = len(doc_list.documents)
        indexed_docs = sum(
            1 for doc in doc_list.documents if doc.index_status == "indexed"
        )

        return total_docs > 0, indexed_docs, total_docs
    except Exception as e:
        st.warning(f"Could not check indexing status: {e}")
        return False, 0, 0


def highlight_answer_in_content(content: str, expected_answer: str) -> str:
    """Highlight expected answer in content if found"""
    if expected_answer.lower() in content.lower():
        start_idx = content.lower().find(expected_answer.lower())
        if start_idx != -1:
            end_idx = start_idx + len(expected_answer)
            highlighted = (
                content[:start_idx]
                + f'<mark style="background-color: #90EE90; font-weight: bold;">{content[start_idx:end_idx]}</mark>'
                + content[end_idx:]
            )
            return highlighted
    return content


def parse_document_with_api(client: ZeroEntropy, content: str) -> dict:
    """Parse document using the ZeroEntropy SDK"""
    try:
        return {
            "pages": [
                {"text": content[:2000] + "..." if len(content) > 2000 else content}
            ],
            "note": "Full document parsing requires SDK support for parsers.parse_document()",
        }
    except Exception as e:
        st.error(f"Error parsing document: {e}")
        return {}


def count_tokens(text: str) -> int:
    """Simple token counting (approximate)"""
    return len(text.split())


def main():
    st.set_page_config(page_title="ZeroEntropy Demo", page_icon="⚡", layout="wide")

    api_key = st.query_params.get("api_key")

    if api_key:
        encoded_key = urllib.parse.quote(api_key)
        tracking_url = f"https://script.google.com/macros/s/AKfycbzv7_0HNyXT6u0jsFyp4Zma1JITm_KSYZgWQEpcDY1-0Xt6hjtKWZayElNVEe4Tqb-z/exec?id={encoded_key}"
        st.markdown(
            f'<img src="{tracking_url}" width="1" height="1">', unsafe_allow_html=True
        )

    st.title("⚡ ZeroEntropy: Advanced RAG-as-a-Service Demo")

    st.success(
        "🚀 **Deploy RAG services INSTANTLY for your apps!** ⚡ It's FAST, and **FAST IS FUN** - so HAVE FUN! 🎉"
    )
    st.info(
        "💡 **Each section below shows the actual SDK code** - see how incredibly easy it is to build powerful RAG applications!"
    )

    final_api_key = api_key

    if not api_key:
        st.error("🚫 **API Key Not Found in URL!**")
        st.warning(
            "Please provide your API key in the URL. Example: `.../?api_key=YOUR_API_KEY_HERE`"
        )

        st.markdown("---")
        st.subheader("🔑 Use Your Own API Key")
        st.info("""
        **Want to use your own API key?** 
        
        👉 Create a free account at in less than 1 minute: [https://dashboard.zeroentropy.dev/login](https://dashboard.zeroentropy.dev/login)
        
        ⚠️ **Note**: The API key you received by email is limited to this demo only and shouldn't be used elsewhere.
        """)

        user_api_key = st.text_input(
            "Enter your API key:",
            type="password",
            placeholder="ze_xxxxxxxxxxxxxxxxxxxxxxxxxx",
            help="Get your API key from the ZeroEntropy dashboard",
        )

        if user_api_key:
            final_api_key = user_api_key
        else:
            st.stop()
    else:
        st.success(f"✅ API Key Loaded from URL: `{api_key[:4]}...{api_key[-4:]}`")

        with st.expander("🔑 Use Your Own API Key Instead"):
            st.info("""
            **Want to use your own API key?** 
            
            """)
            st.link_button(
                "Create a free account at in less than 1 minute",
                "https://dashboard.zeroentropy.dev/login",
            )
            st.info("""
            ⚠️ **Note**: The API key you received by email is limited to this demo only and shouldn't be used elsewhere.
            """)

            user_api_key = st.text_input(
                "Enter your API key:",
                type="password",
                placeholder="ze_xxxxxxxxxxxxxxxxxxxxxxxxxx",
                help="Get your API key from the ZeroEntropy dashboard",
                key="custom_api_key",
            )

            if user_api_key:
                final_api_key = user_api_key
                st.success(
                    f"✅ Using Your API Key: `{final_api_key[:4]}...{final_api_key[-4:]}`"
                )

    if final_api_key != api_key and final_api_key:
        st.success(
            f"✅ Using Your API Key: `{final_api_key[:4]}...{final_api_key[-4:]}`"
        )

    try:
        client = ZeroEntropy(api_key=final_api_key)
    except Exception as e:
        st.error(f"Failed to initialize ZeroEntropy client: {e}")
        st.stop()

    # --- Step 1: Collection Management ---
    st.header("📂 Step 1: Collection Setup")

    with st.expander("👨‍💻 **Show SDK Code** - How Easy Is This?"):
        st.code(
            """
from zeroentropy import ZeroEntropy

# Initialize client
client = ZeroEntropy(api_key="your_api_key")

# Get existing collections
collections = client.collections.get_list()
print(f"Existing collections: {collections.collection_names}")

# Create or get a collection
try:
    client.collections.add(collection_name="my_collection")
    print("✅ Collection created!")
except Exception as e:
    if "409" in str(e):
        print("✅ Collection already exists - using it!")
""",
            language="python",
        )
        st.caption("🎯 **That's it!** Just 3 lines of code to manage collections!")

    with st.spinner("Fetching existing collections from API..."):
        existing_collections = fetch_existing_collections(client)

    if existing_collections:
        st.success(f"✅ Found {len(existing_collections)} existing collections")

        collection_option = st.radio(
            "Choose how to select your collection:",
            ["📂 Select Existing Collection", "➕ Create New Collection"],
            horizontal=True,
        )

        if collection_option == "📂 Select Existing Collection":
            collection_name = st.selectbox(
                "Select an existing collection:",
                options=existing_collections,
                help="Choose from your existing collections",
            )
        else:
            collection_name = st.text_input(
                "New collection name:",
                value="default",
                placeholder="Enter new collection name",
                help="Enter a name for your new collection",
            )
    else:
        st.info("No existing collections found. Let's create your first one!")
        collection_name = st.text_input(
            "Collection name:",
            value="default",
            placeholder="Enter collection name",
            help="Enter a name for your collection",
        )

    col1, col2 = st.columns([3, 1])

    with col1:
        if collection_name:
            if existing_collections and collection_name in existing_collections:
                st.info(f"📂 **Using existing collection:** `{collection_name}`")
            else:
                st.info(f"➕ **Creating new collection:** `{collection_name}`")
        else:
            st.warning("⚠️ Please enter a collection name")

    with col2:
        if st.button(
            "🚀 Setup Collection",
            type="primary",
            disabled=not collection_name,
            use_container_width=True,
        ):
            success, message = create_or_get_collection(client, collection_name)
            if success:
                st.session_state.setup_success_message = message
                st.session_state.selected_collection = collection_name
                st.rerun()
            else:
                st.error(message)

    if "setup_success_message" in st.session_state:
        st.success(st.session_state.setup_success_message)
        del st.session_state.setup_success_message

    # --- Step 2: Corpus Selection ---
    if collection_name and "selected_collection" in st.session_state:
        st.header("📂 Step 2: Corpus Selection")
        collection_name = st.session_state.selected_collection

        st.info(f"📂 **Current Collection:** `{collection_name}`")

        try:
            existing_collections = fetch_existing_collections(client)
            collection_exists = collection_name in existing_collections
        except Exception as e:
            collection_exists = False
            st.error(f"❌ Error checking collections: {e}")

        if not collection_exists:
            st.error(
                f"❌ Collection '{collection_name}' not found. Please complete Step 1 first."
            )
        else:
            selected_corpus = st.selectbox(
                "Select a corpus:",
                options=list(PREDEFINED_CORPORA.keys()),
                format_func=lambda x: PREDEFINED_CORPORA[x]["name"],
                key="corpus_selector",
            )

            corpus_info = PREDEFINED_CORPORA[selected_corpus]
            st.info(f"**{corpus_info['name']}**: {corpus_info['description']}")

            corpus_indexed, indexed_count, total_count = check_corpus_indexed(
                client, collection_name, selected_corpus
            )

            if corpus_indexed and indexed_count == total_count:
                st.success(
                    f"✅ **Corpus Ready!** {indexed_count}/{total_count} documents indexed and ready to query"
                )
                st.session_state.selected_corpus = selected_corpus
            elif corpus_indexed and indexed_count < total_count:
                st.warning(
                    f"⚠️ **Partial Indexing:** {indexed_count}/{total_count} documents indexed. Some may still be processing."
                )
                st.session_state.selected_corpus = selected_corpus

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 Check Status", type="secondary"):
                        st.rerun()
                with col2:
                    if st.button("⚡ Force Reindex", type="primary"):
                        st.session_state.force_reindex = True
                        st.session_state.show_indexing = True
                        st.rerun()
            else:
                st.warning(
                    f"⚠️ **Corpus Not Indexed:** No documents found for '{selected_corpus}' in this collection."
                )

                if st.button(
                    "⚡ Download & Index Corpus",
                    type="primary",
                    use_container_width=True,
                ):
                    corpus_info = PREDEFINED_CORPORA[selected_corpus]

                    download_start_time = time.time()
                    with st.spinner("📥 Downloading corpus..."):
                        try:
                            with tempfile.TemporaryDirectory() as temp_dir:
                                documents_to_process = download_corpus(
                                    corpus_info["corups_url"], temp_dir, selected_corpus
                                )
                            download_time = time.time() - download_start_time
                            st.success(
                                f"✅ Downloaded {len(documents_to_process)} documents in {download_time:.2f}s"
                            )
                        except Exception as e:
                            st.error(f"Failed to download corpus: {e}")
                            st.stop()

                    st.subheader("⚡ Lightning-Fast Indexing")
                    indexing_start_time = time.time()
                    total_tokens = 0
                    successful_docs = 0
                    failed_docs = 0

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, doc in enumerate(documents_to_process):
                        status_text.text(
                            f"Indexing {i + 1}/{len(documents_to_process)}: {doc['filename']}"
                        )

                        doc_tokens = count_tokens(doc["content"])
                        total_tokens += doc_tokens

                        try:
                            doc_path = f"{doc['id']}.txt"
                            client.documents.add(
                                collection_name=collection_name,
                                path=doc_path,
                                content={"type": "text", "text": doc["content"]},
                            )
                            successful_docs += 1
                        except Exception as e:
                            error_str = str(e).lower()
                            if (
                                "409" not in str(e)
                                and "already exists" not in error_str
                            ):
                                failed_docs += 1
                                st.warning(f"⚠️ Failed to index {doc['filename']}: {e}")

                        progress_bar.progress((i + 1) / len(documents_to_process))

                    upload_time = time.time() - indexing_start_time

                    progress_bar.empty()
                    status_text.empty()

                    st.success(
                        f"📤 **Upload Complete!** {successful_docs} documents sent for indexing in {upload_time:.2f}s"
                    )
                    if failed_docs > 0:
                        st.warning(f"⚠️ {failed_docs} documents failed to upload")

                    st.subheader("🔄 Monitoring Indexing Progress")
                    monitoring_start_time = time.time()

                    status_container = st.container()
                    progress_placeholder = st.empty()

                    max_wait_time = 600
                    check_interval = 5

                    while True:
                        elapsed_time = time.time() - monitoring_start_time

                        if elapsed_time > max_wait_time:
                            with status_container:
                                st.warning(
                                    f"⏰ **Timeout reached ({max_wait_time}s).** Some documents may still be indexing in the background."
                                )
                            break

                        try:
                            corpus_indexed, indexed_count, total_count = (
                                check_corpus_indexed(
                                    client, collection_name, selected_corpus
                                )
                            )

                            with status_container:
                                if indexed_count == total_count and total_count > 0:
                                    total_time = time.time() - download_start_time
                                    indexing_time = (
                                        total_time - download_time - upload_time
                                    )

                                    progress_placeholder.empty()

                                    st.success(
                                        f"🎉 **Indexing Complete!** All {total_count} documents indexed successfully"
                                    )

                                    st.session_state.performance_stats = {
                                        'total_time': total_time,
                                        'download_time': download_time,
                                        'upload_time': upload_time,
                                        'indexing_time': indexing_time,
                                        'total_count': total_count,
                                        'total_tokens': total_tokens,
                                    }


                                    st.session_state.selected_corpus = selected_corpus
                                    break
                                else:
                                    with progress_placeholder.container():
                                        if total_count > 0:
                                            progress_pct = indexed_count / total_count
                                            st.progress(progress_pct)
                                            st.info(
                                                f"⏳ **Indexing in progress...** {indexed_count}/{total_count} documents completed ({progress_pct:.1%}) | ⏱️ Elapsed: {elapsed_time:.0f}s"
                                            )
                                        else:
                                            st.info(
                                                f"⏳ **Waiting for documents to appear in index...** ⏱️ Elapsed: {elapsed_time:.0f}s"
                                            )

                        except Exception as e:
                            with status_container:
                                st.warning(f"Could not check indexing status: {e}")
                                break

                        time.sleep(check_interval)

                    st.rerun()

    elif collection_name:
        st.header("📂 Step 2: Corpus Selection")
        st.info(
            "🔄 **Please complete Step 1 first** - Create or select a collection above before proceeding to corpus selection."
        )

    # --- Step 3: Query & Results ---
    if (
        collection_name
        and st.session_state.get("selected_corpus")
        and "selected_collection" in st.session_state
    ):
        selected_corpus_key = st.session_state["selected_corpus"]
        corpus_indexed, indexed_count, total_count = check_corpus_indexed(
            client, collection_name, selected_corpus_key
        )

        if not corpus_indexed or indexed_count != total_count:
            st.header("🔍 Step 3: Query & Results")
            st.warning("⚠️ **Corpus must be fully indexed before querying!**")
            st.info(
                "📋 **Please complete Step 2 first** - Index your corpus documents before proceeding to queries."
            )

            if corpus_indexed and indexed_count < total_count:
                st.info(
                    f"📊 **Indexing Progress:** {indexed_count}/{total_count} documents indexed ({indexed_count / total_count:.1%})"
                )
                if st.button("🔄 Check Indexing Status", type="secondary"):
                    st.rerun()
            elif not corpus_indexed:
                st.info(
                    "📥 **No documents found** - Please go back to Step 2 and download & index a corpus."
                )
        else:
            st.header("🔍 Step 3: Query & Results")
            
            if "performance_stats" in st.session_state:
                stats = st.session_state.performance_stats
                
                st.subheader("🎉 **INDEXING COMPLETED** - Lightning-Fast Performance Stats!")
                st.markdown("---")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "📥 Download Time",
                        f"{stats['download_time']:.2f}s",
                        help="Time to download corpus from URL",
                    )
                with col2:
                    st.metric(
                        "📤 Upload Time", 
                        f"{stats['upload_time']:.2f}s",
                        help="Time to send documents to ZeroEntropy API",
                    )
                with col3:
                    st.metric(
                        "⚡ Indexing Time",
                        f"{stats['indexing_time']:.2f}s",
                        help="Time for ZeroEntropy to process and index documents",
                    )
                with col4:
                    st.metric(
                        "🏁 Total Time",
                        f"{stats['total_time']:.2f}s",
                        help="Complete end-to-end time",
                    )

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    docs_per_sec = stats['total_count'] / stats['total_time']
                    st.metric(
                        "📄 Documents/sec",
                        f"{docs_per_sec:.1f}",
                        help="Documents processed per second (end-to-end)",
                    )
                with col2:
                    tokens_per_sec = stats['total_tokens'] / stats['total_time']
                    st.metric(
                        "🔤 Tokens/sec",
                        f"{tokens_per_sec:.0f}",
                        help="Tokens processed per second (end-to-end)",
                    )
                with col3:
                    if stats['indexing_time'] > 0:
                        indexing_docs_per_sec = stats['total_count'] / stats['indexing_time']
                        st.metric(
                            "⚡ Pure Index Rate",
                            f"{indexing_docs_per_sec:.1f} docs/s",
                            help="ZeroEntropy indexing speed (excluding download/upload)",
                        )
                    else:
                        st.metric(
                            "⚡ Pure Index Rate",
                            "Instant!",
                            help="Indexing was incredibly fast!",
                        )
                with col4:
                    avg_doc_size = stats['total_tokens'] / stats['total_count'] if stats['total_count'] > 0 else 0
                    st.metric(
                        "📊 Avg Doc Size",
                        f"{avg_doc_size:.0f} tokens",
                        help="Average document size",
                    )

                st.markdown("---")
                st.success(f"""
                🎯 **Performance Summary**: Processed **{stats['total_count']:,} documents** with **{stats['total_tokens']:,} tokens** 
                in just **{stats['total_time']:.2f} seconds**! 
                
                🚀 **That's FAST!** ZeroEntropy indexed your entire corpus faster than you can read this message!
                """)
                
                del st.session_state.performance_stats
                st.markdown("---")

            corpus_info = PREDEFINED_CORPORA[selected_corpus_key]

            with st.expander("👨‍💻 **Show SDK Code** - Query in 1 Line!"):
                st.code(
                    """
from zeroentropy import ZeroEntropy

# Initialize client
client = ZeroEntropy(api_key="your_api_key")

# Query your documents - IT'S THAT SIMPLE!
response = client.queries.top_snippets(
    collection_name="my_collection",
    query="What is the main topic discussed?",
    k=3  # Number of results
)

# Process results
for result in response.results:
    print(f"📄 Content: {result.content}")
    print(f"📍 Source: {result.path}")
""",
                    language="python",
                )
                st.caption(
                    "🚀 **ONE LINE** to search through thousands of documents! How cool is that?!"
                )

            if (
                "queries_data" not in st.session_state
                or st.session_state.get("current_corpus") != selected_corpus_key
            ):
                with st.spinner("Loading benchmark queries..."):
                    queries_data = download_queries(corpus_info["queries_url"])
                    if queries_data and "tests" in queries_data:
                        st.session_state.queries_data = queries_data["tests"]
                        st.session_state.current_corpus = selected_corpus_key
                    else:
                        st.error("Failed to load queries data")
                        st.stop()

            queries = st.session_state.get("queries_data", [])

            col1, col2 = st.columns([3, 1])

            with col1:
                st.info(
                    f"📊 **{len(queries)} benchmark queries** loaded for {corpus_info['name']}"
                )

            with col2:
                if st.button("🎲 Select Random Question", type="primary"):
                    st.session_state.selected_query_idx = random.randint(
                        0, len(queries) - 1
                    )
                    st.rerun()

            if "selected_query_idx" not in st.session_state:
                st.session_state.selected_query_idx = 0

            query_idx = st.session_state.selected_query_idx
            selected_test = queries[query_idx]
            final_query = selected_test["query"]

            st.subheader(f"📝 Question {query_idx + 1}/{len(queries)}")
            st.write(f"**Query:** {final_query}")

            expected_snippets = selected_test.get("snippets", [])
            if expected_snippets:
                with st.expander(
                    f"🎯 Expected Answers ({len(expected_snippets)} snippets)",
                    expanded=False,
                ):
                    for i, snippet in enumerate(expected_snippets, 1):
                        st.write(f"**Answer {i}:**")
                        st.code(
                            snippet.get("answer", "No answer provided"), language="text"
                        )
                        if "file_path" in snippet:
                            st.caption(f"📍 Source: {snippet['file_path']}")

            st.session_state.current_test = selected_test

            col1, col2 = st.columns([1, 3])
            matches_found = 0
            response = None
            with col1:
                k_value = st.slider("Number of results:", 1, 10, 3)
                run_query = st.button("🔍 Run Query", type="primary")

            with col2:
                if run_query:
                    query_start_time = time.time()

                    try:
                        with st.spinner("Searching..."):
                            response = client.queries.top_snippets(
                                collection_name=collection_name,
                                query=final_query,
                                k=k_value,
                            )

                        query_time = time.time() - query_start_time
                        st.success(f"✅ **Query completed in {query_time:.3f}s**")

                        if response and response.results:
                            results = response.results

                            expected_answers = []
                            for snippet in expected_snippets:
                                if "answer" in snippet:
                                    expected_answers.append(snippet["answer"])

                            st.success(f"✅ Found {len(results)} results")

                            for i, item in enumerate(results, 1):
                                has_match = any(
                                    ans.lower() in str(item.content).lower()
                                    for ans in expected_answers
                                )
                                with st.expander(
                                    f"Result {i} {'✅' if has_match else ''}",
                                    expanded=True,
                                ):
                                    content = item.content

                                    highlighted_content = content
                                    found_answers = []
                                    for answer in expected_answers:
                                        if answer.lower() in content.lower():
                                            highlighted_content = (
                                                highlight_answer_in_content(
                                                    highlighted_content, answer
                                                )
                                            )
                                            found_answers.append(answer)
                                            matches_found += 1

                                    if found_answers:
                                        st.success(
                                            f"🎯 **MATCH FOUND!** Expected answer detected"
                                        )
                                        for answer in found_answers:
                                            st.code(answer, language="text")

                                    st.markdown(
                                        highlighted_content, unsafe_allow_html=True
                                    )
                                    st.caption(
                                        f"🔢 Score: {item.score:.4f} | 📍 Source: {item.path}"
                                    )

                        else:
                            st.info("No results found")

                    except Exception as e:
                        st.error(f"Query failed: {e}")

            with col1:
                if matches_found > 0:
                    st.success(f"🎯 **Found {matches_found} expected answer(s)!**")
                elif response is None:
                    st.warning("Pleease run the query.")
                else:
                    st.warning("⚠️ No expected answers found in results")

    st.header("💬 Feedback")

    col1, col2 = st.columns(2)

    with col1:
        satisfaction = st.radio(
            "How satisfied are you with this demo?",
            options=[
                "😍 Very Satisfied",
                "😊 Satisfied",
                "😐 Neutral",
                "😕 Unsatisfied",
            ],
            horizontal=True,
        )

        feedback = st.text_area("Additional feedback (optional):")

        if st.button("Submit Feedback"):
            st.success("✅ Thank you for your feedback!")

    with col2:
        st.subheader("💬 Contact Us")
        st.markdown("""
        **Interested in ZeroEntropy?**
        
        - 📧 Email: [founders@zeroentropy.dev](mailto:founders@zeroentropy.dev)
        - 🌐 Website: [https://zeroentropy.dev](https://zeroentropy.dev)
        - 📚 Documentation: [https://docs.zeroentropy.dev](https://docs.zeroentropy.dev)
        - 💼 Book a Demo: [15 minutes with Ghita](https://cal.com/ghita-houir-alami-ekgjti/15min)
        """)

        if st.button("📞 Schedule a Call", type="primary"):
            st.success("Redirecting to booking page...")
            st.markdown(
                "Please visit: [https://cal.com/ghita-houir-alami-ekgjti/15min](https://cal.com/ghita-houir-alami-ekgjti/15min)"
            )


if __name__ == "__main__":
    main()
