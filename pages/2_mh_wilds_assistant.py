import streamlit as st
from src.model import Model


@st.cache_resource
def load_model():
    return Model(api_key=st.secrets["OPENAI_API_KEY"], k=50)


model = load_model()
db_csv = model.prepare_csv()

st.set_page_config(
    page_title="The Guild Oracle",
)

st.title("The Guild Oracle")

with st.form("my_form"):
    text = st.text_area(label="Ask your question about Monster Hunter Wilds to The Guild Oracle.")
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.info(model.rag(db_faiss=db_csv, query=text))
