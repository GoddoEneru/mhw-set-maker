# Monster Hunter Wilds – Armor Set Maker & AI Assistant

Build your best gear. Ask questions.  
A simple app for **Monster Hunter Wilds** fans – featuring a **Armor Set Maker** and an **AI-powered assistant** trained on game data and guides.

---

## Features

### Armor Set Maker
Create optimized gear:
- Pick the skills you want
- Prioritize an higher defense or more decorations slots
- Optimize your gear for any monster, quest, or playstyle

### LLM Assistant (RAG-powered) ! WORK IN PROGRESS !
Ask anything about the game:
- Monster weaknesses
- Material drop rates
- Armor set bonuses
- Farming tips
- Game lore

Powered by **RAG (Retrieval-Augmented Generation)** using a custom knowledge base of curated wiki and guide content.

---

## Tech Stack

- **Python**
- **Streamlit** – for the UI
- **LLM (OpenAI)** – for question answering
- **LangChain** – for RAG pipelines
- **FAISS** – for vector search
- **Pandas / NumPy** – for data processing
- **BeautifulSoup** - for data scraping

---

## 🛠 Installation

1. Clone this project
```bash
git clone https://github.com/GoddoEneru/mhw-set-maker.git
cd mhw-set-maker
```
2. Create your virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install all required Python Libraries
```bash
pip install -r requirements.txt
```

4. Create a ".streamlit" folder in the working directory with a "secrets.toml" file and put you OpenAI api key in it
```
OPENAI_API_KEY = "your-openai-api-key"
```

5. Run the app and have fun with it !
```bash
streamlit run app.py
```
