import streamlit as st
import pandas as pd
from src.set_maker import SetMaker


df_armors = pd.read_csv("src/data/armors.csv")
df_talismans = pd.read_csv("src/data/talismans.csv")
df_skills = pd.read_csv("src/data/skills.csv")
set_maker = SetMaker()

st.set_page_config(
    page_title="Hunter Set Generator",
)

st.title("Hunter Set Generator")

with st.container(border=True):
    necessary_skills = st.multiselect(
        label="Choose all skills you want in your set !",
        options=df_skills['Skill'].values,
        placeholder="Skills will be prioritized in selection order"
        )

    sort_on = st.selectbox(
        label="Choose what is more important to you after skills",
        options=['defense', 'decorations']
        )

clicked = st.button(
    label="Generate Armor Set",
)

st.divider()

if clicked and len(necessary_skills) == 0:
    st.write("Choose skills before trying to generate an armor set.")
elif clicked:
    df_armors = set_maker.add_decorations_score_col(df_armors)
    filtered_df_armors, filtered_df_talismans = set_maker.filter_relevant_armors_and_talismans(
        necessary_skills, df_armors, df_talismans)
    df_best_armors = set_maker.get_best_armor_for_each_type(df_armors, sort_on)
    armor_sets = set_maker.make_armor_sets(filtered_df_armors, filtered_df_talismans, df_best_armors)
    relevant_sets = set_maker.filter_valid_armor_sets(armor_sets, df_skills)
    best_set = set_maker.get_best_set(relevant_sets, necessary_skills, sort_on)
    st.write(best_set)
