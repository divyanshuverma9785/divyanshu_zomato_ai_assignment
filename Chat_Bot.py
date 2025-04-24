import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import warnings, os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

data_directory = os.path.join(os.path.dirname(__file__), "data")

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Load the vector store from disk
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(embedding_function=embedding_model, persist_directory=data_directory)

# Initialize the Hugging Face Hub LLM
hf_hub_llm = HuggingFaceHub(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    model_kwargs={"temperature": 0.7, "max_new_tokens": 1024},
)

prompt_template = """
As a knowledgeable restaurant assistant, your role is to accurately interpret food and restaurant queries and 
provide responses using our specialized restaurant database. Follow these directives to ensure optimal user interactions:

1. Precision in Answers: Respond solely with information directly relevant to the user's query from our restaurant database. 
   Refrain from making assumptions or adding extraneous details.
   
2. Topic Relevance: Limit your expertise to specific restaurant-related areas:
   - Restaurant Information (location, hours, contact)
   - Menu Items and Categories
   - Food Descriptions and Ingredients
   - Pricing Information
   - Dietary Preferences (Veg/Non-Veg, Spice Levels)
   
3. Handling Off-topic Queries: For questions unrelated to restaurants or food, politely inform the user that the query 
   is outside the chatbot's scope and suggest redirecting to restaurant-related inquiries.
   
4. Contextual Accuracy: Ensure responses are directly related to the restaurant query, utilizing only pertinent 
   information from our database.
   
5. Relevance Check: If a query does not align with our restaurant database, guide the user to refine their 
   question or politely decline to provide an answer.
   
6. Streamlined Communication: Eliminate any unnecessary comments or closing remarks from responses. Focus on
   delivering clear, concise, and direct answers.
   
7. Personalized Recommendations: When appropriate, provide personalized food recommendations based on user preferences.

Restaurant Query:
{context}

Question: {question}

Answer:
"""

custom_prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

rag_chain = RetrievalQA.from_chain_type(
    llm=hf_hub_llm, 
    chain_type="stuff", 
    retriever=vector_store.as_retriever(top_k=5),  # Increased to fetch top 5 results to cover multiple restaurants
    chain_type_kwargs={"prompt": custom_prompt})

def get_response(question):
    result = rag_chain({"query": question})
    response_text = result["result"]
    answer_start = response_text.find("Answer:") + len("Answer:")
    answer = response_text[answer_start:].strip()
    return answer

# Streamlit app
# Remove whitespace from the top of the page and sidebar
st.markdown(
    """
        <style>
            .appview-container .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
        </style>""",
    unsafe_allow_html=True,
)

st.markdown("""
    <h3 style='text-align: left; color: black; padding-top: 35px; border-bottom: 3px solid orange;'>
        Discover Local Restaurants & Menus 🍽️🥘
    </h3>""", unsafe_allow_html=True)

side_bar_message = """
Hi! 👋 I'm your restaurant guide for Roorkee. What would you like to know about local restaurants?

Here are some areas you might be interested in:
1. **Restaurant Information** 🏢
2. **Menu Recommendations** 🍲
3. **Vegetarian Options** 🥗
4. **Spice Level Preferences** 🌶️
5. **Popular Dishes** ⭐

Feel free to ask me anything about the restaurants in our database!
"""

with st.sidebar:
    st.title('🤖FoodBot: Your Local Restaurant Guide')
    st.markdown(side_bar_message)

initial_message = """
    Hi there! I'm your FoodBot 🤖 
    Here are some questions you might ask me:\n
    🍽️ What restaurants are available in Roorkee?\n
    🍽️ Tell me about Hotel Prakash's menu\n
    🍽️ What vegetarian options are available?\n
    🍽️ What are the operating hours of restaurants in Roorkee?\n
    🍽️ Can you recommend some spicy dishes?\n
    🍽️ What's the price range for rolls at Hotel Prakash?
"""

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]
    
st.button('Clear Chat', on_click=clear_chat_history)

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Finding the best food recommendations for you..."):
            response = get_response(prompt)
            placeholder = st.empty()
            full_response = response
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
