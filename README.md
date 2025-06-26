# ZeroEntropy Demo Application

⚡ **Advanced RAG-as-a-Service Demo** - Deploy RAG services instantly for your applications!

This is a Streamlit-based demo application showcasing the capabilities of ZeroEntropy, a powerful RAG (Retrieval-Augmented Generation) platform that enables instant deployment of document search and question-answering services.

## Features

🚀 **Instant RAG Deployment** - Set up document collections and search services in minutes  
📚 **Legal Document Corpora** - Pre-configured datasets including ContractNLI, CUAD, MAUD, and PrivacyQA  
🔍 **Advanced Search** - Semantic search capabilities with document retrieval and ranking  
❓ **Question Answering** - Interactive Q&A interface with highlighted answers  
📊 **Real-time Analytics** - Collection management and indexing status monitoring  

## Supported Datasets

- **ContractNLI** - Legal Contract Natural Language Inference Dataset
- **CUAD** - Contract Understanding Atticus Dataset  
- **MAUD** - Merger Agreement Understanding Dataset
- **PrivacyQA** - Question Answering for Privacy Policies

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd zeroentropy
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Demo

1. Start the Streamlit application:
```bash
streamlit run demoapp.py
```

2. Access the application in your browser (typically at `http://localhost:8501`)

3. Provide your ZeroEntropy API key either:
   - As a URL parameter: `http://localhost:8501/?api_key=YOUR_API_KEY_HERE`
   - Or enter it directly in the application interface

### Key Functionality

- **Collection Management**: Create and manage document collections
- **Document Upload**: Upload and index your own documents
- **Corpus Loading**: Load predefined legal document datasets
- **Search Interface**: Perform semantic searches across your collections
- **Q&A Testing**: Test question-answering capabilities with benchmarks

## Dependencies

- `streamlit` - Web application framework
- `zeroentropy` - ZeroEntropy SDK for RAG services
- `requests` - HTTP library for API calls

## API Integration

This demo showcases the ZeroEntropy SDK with examples of:

- Collection creation and management
- Document uploading and indexing
- Semantic search queries
- Question-answering workflows
- Real-time status monitoring

## Getting Started

1. Get your ZeroEntropy API key from the platform
2. Run the demo application
3. Try the predefined legal datasets or upload your own documents
4. Experiment with search queries and Q&A functionality

---

⚡ **FAST IS FUN** - Experience the speed and power of ZeroEntropy RAG services! 