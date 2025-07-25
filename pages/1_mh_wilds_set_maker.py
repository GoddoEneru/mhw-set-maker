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

    newline = "\n"
    cols_skills = [col for col in best_set.columns if "skills" in col]
    skills = {col_skill.split('_')[1]: best_set[col_skill].item() for col_skill in cols_skills}

    st.header("Generated armor set")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Armor pieces")
        st.markdown(
            f"""
            - Head : **{best_set['head'].item()}**
            - Chest : **{best_set['chest'].item()}**
            - Arm : **{best_set['arm'].item()}**
            - Waist : **{best_set['waist'].item()}**
            - Leg : **{best_set['leg'].item()}**
            - Talisman : **{best_set['talisman'].item()}**
            """
            )

    with col2:
        st.subheader("Skills")
        st.markdown(
            f"""
            {newline.join(f"- {key} : **level {int(value)}**" for key, value in skills.items())}
            """
        )

    with col3:
        st.subheader("Stats")
        st.markdown(
            f"""
            - Defense : **{best_set['defense'].item()}**
            - Number of size 1 decorations : **{best_set['nb_decorations_size_1'].item()}**
            - Number of size 2 decorations : **{best_set['nb_decorations_size_2'].item()}**
            - Number of size 3 decorations : **{best_set['nb_decorations_size_3'].item()}**
            """
        )
