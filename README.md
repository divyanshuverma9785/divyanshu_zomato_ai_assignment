# Roorkee Restaurants RAG Chatbot

## Overview
This project provides a fully local, open-source RAG (Retrieval Augmented Generation) conversational assistant that answers queries about top restaurants and their menus in Roorkee, India. The system uses scraped restaurant data, advanced text embeddings, and a Hugging Face LLM to power natural, context-rich food and restaurant Q&A.

---

## Features
- Answers queries about menu items, dietary options, pricing, operating hours, and restaurant comparisons for Roorkee restaurants
- Handles ambiguous, out-of-scope, or off-topic questions politely
- Personalized menu and dish suggestions
- Conversation history and reset functionality (Streamlit UI)

---
## How to Scrape the Knowledge Base

To create or update your local `top_5_roorkee_resturants_data.json` (restaurant knowledge base):

1. **Open Jupyter Notebook or Python** and copy in the functions from `zomato_bulk_scraper.py`.
2. **Edit or extend** the `restaurant_urls` dictionary with all the Zomato restaurant URLs you want.
3. **Call** `scrape_bulk_zomato(restaurant_urls, output_path="top_5_roorkee_resturants_data.json")`.

This will create the file your chatbot pipeline expects, with all fields (`name`, `location`, `contact`, `operating_hours`, `menu`, etc.) perfectly matched to the RAG knowledge base schema.

![image](https://github.com/user-attachments/assets/5a933e7b-18de-4121-8b97-62c475cf7617) 


---

## Architecture

![Architecture Diagram](uploads/Bot_Architecture.png)

- **Data Pipeline**: Scraped JSON is flattened, preprocessed, and turned into embedding vectors
- **Retrieval**: Chroma vector store finds top relevant menu/restaurant chunks for a user query
- **Generation**: Hugging Face LLM generates a well-structured answer using retrieved context and a custom prompt template
- **User Interface**: Streamlit chat app simulates an assistant experience, supports history and feedback

---

## Data Schema
Your main data file should be named `top_5_roorkee_resturants_data.json` and be placed in the `uploads/` directory.

Example entry:
```json
[
  {
    "restaurant": {
      "name": "Hotel Prakash",
      "location": "19, Civil lines, Roorkee",
      "contact": "+917895885082",
      "operating_hours": "10 AM - 11 PM"
    },
    "menu": [
      {
        "category": "Exclusive 100% Wheat Paratha Kaathi Rolls",
        "items": [
          {
            "name": "Paneer Wheat Roll",
            "price": "₹169",
            "description": "Indulge in...",
            "veg_nonveg": "Veg",
            "spice_level": "Normal"
          }
        ]
      }
    ]
  }
]
```

---

## Setup Instructions

### 1. Clone and Install
```bash
# (Optionally) create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. HuggingFace API Token
- Get a free [Hugging Face API token](https://huggingface.co/settings/tokens) if you don't have one.
- Create a `.env` file in the root with:
```
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

### 3. Prepare Data
- Make sure `top_5_roorkee_resturants_data.json` is present in the `uploads/` folder (see schema above).

If you want to reproduce the dataset with fresh scraping:

```bash
python uploads/roorkee_resturant_scraper.py
```
Then (inside a Python shell or by editing the file), call:

```python
# At the bottom of uploads/roorkee_resturant_scraper.py:
from roorkee_resturant_scraper import scrape_all_restaurants
scrape_all_restaurants()  # This will export uploads/top_5_roorkee_resturants_data.json
```

The code scrapes each target restaurant's full menu and info, extracting details like location, contact, operating_hours, and all menu items, matching perfectly the schema required by the downstream bot and knowledge base builder.

### 4. Build Knowledge Base (Vector DB)
```bash
python uploads/vector_embeddings.py
```

- This creates the Chroma vector DB in `uploads/data/`.

### 5. Launch the Chatbot
```bash
streamlit run uploads/RestaurantBot.py
```
- Open the displayed local URL to start chatting!

---

## Typical Questions (Try these!)
- What restaurants are available in Roorkee?
- Tell me about Hotel Prakash's menu
- What vegetarian options are available?
- What are the operating hours of restaurants in Roorkee?
- Can you recommend some spicy dishes?
- What's the price range for rolls at Hotel Prakash?
- Compare vegetarian options at Foodbay and Pizza Hut
- Which restaurant offers the most affordable thali?
- Are there vegan or gluten-free items?

---

## Troubleshooting
- **No answers**: Double-check the data JSON and rerun `vector_embeddings.py` after making updates
- **Model/token errors**: Ensure your Hugging Face key is set and valid, and you are not rate-limited
- **UI problems**: Restart Streamlit, check for missing dependencies (see requirements.txt)

---

## System Design, Choices & Improvements
- Chunked each menu item + context as an embedding document for precise retrieval
- Uses all free-tier Hugging Face models by default
- Easy to add more restaurants: update the JSON and rerun embedding
- Future: Add richer metadata, dietary tags, feedback loop, or deploy online

---

## Credits
- Built with LangChain, ChromaDB, Hugging Face, and Streamlit
- See `uploads/roorkee_resturant_scraper.py` for scraping methodology
