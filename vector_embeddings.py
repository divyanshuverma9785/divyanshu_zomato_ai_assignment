import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import os
from dotenv import load_dotenv
from langchain.docstore.document import Document

# Load environment variables from .env file
load_dotenv()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Load the knowledge base JSON
data_path = os.path.join(os.path.dirname(__file__), 'uploads', 'top_5_roorkee_resturants_data.json')
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Data normalization and flattening
text_docs = []
for entry in data:
    rest = entry["restaurant"]
    menu = entry["menu"]
    for cat in menu:
        category = cat.get('category', 'Uncategorized')
        for item in cat.get('items', []):
            doc_text = (
                f"Restaurant: {rest['name']}\n"
                f"Location: {rest.get('location','')}\n"
                f"Contact: {rest.get('contact','')}\n"
                f"Operating Hours: {rest.get('operating_hours','')}\n"
                f"Category: {category}\n"
                f"Item: {item['name']}\n"
                f"Price: {item['price']}\n"
                f"Vegetarian: {item.get('veg_nonveg', 'Unknown')}\n"
                f"Spice Level: {item.get('spice_level', 'Unknown')}\n"
                f"Description: {item['description']}"
            )
            text_docs.append(Document(page_content=doc_text))

# Split the texts
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
texts = text_splitter.split_documents(text_docs)

# Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Build/persist vector store
persist_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'data')
os.makedirs(persist_dir, exist_ok=True)
vector_store = Chroma.from_documents(documents=texts, embedding=embedding_model, persist_directory=persist_dir)
vector_store.persist()
print(f"[SUCCESS] Vector DB created with {len(texts)} documents in {persist_dir}")

# Validate the setup with a sample query
test_query = "What are the vegetarian options at Hotel Prakash?"
retriever = vector_store.as_retriever()
results = retriever.get_relevant_documents(test_query)
print("\nSample retrieval results:\n----------------------")
for doc in results[:3]:
    print(doc.page_content + "\n---")
