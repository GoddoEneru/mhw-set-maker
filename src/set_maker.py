import pandas as pd
import numpy as np
from copy import deepcopy

from src.armor_set import ArmorSet


class SetMaker:
    def __init__(self):
        self.df_armors = pd.read_csv("src/data/armors.csv")
        self.df_talismans = pd.read_csv("src/data/talismans.csv")
        self.df_skills = pd.read_csv("src/data/skills.csv")

    def add_decorations_score_col(self, df_armors):
        decoration_cols_names = ['Decoration_slot_1_size', 'Decoration_slot_2_size', 'Decoration_slot_3_size']
        df_armors[decoration_cols_names] = df_armors[decoration_cols_names].fillna(0)
        df_armors['Decorations_score'] = df_armors.apply(
            lambda x: x['Decoration_slot_1_size'] + x['Decoration_slot_2_size'] + x['Decoration_slot_3_size'], axis=1)
        return df_armors

    def filter_csv_on_skills_name(self, skills, df_armors, df_talismans):
        filter = df_armors['Skill_1_name'].isin(skills)\
            | df_armors['Skill_2_name'].isin(skills)\
            | df_armors['Skill_3_name'].isin(skills)
        filtered_df_armors = df_armors.loc[filter]

        filter = df_talismans['Skill_name'].isin(skills)
        filtered_df_talismans = df_talismans.loc[filter]
        filtered_df_talismans = filtered_df_talismans.sort_values(by=['Skill_lvl'], ascending=False)
        filtered_df_talismans = filtered_df_talismans.groupby('Skill_name').apply(
            lambda x: x.iloc[0]).reset_index(drop=True)

        return filtered_df_armors, filtered_df_talismans

    def get_best_armor_for_each_type(self, df_armors, sort_on='defense'):
        sorted_df_armors = df_armors.copy()
        match sort_on:
            case "defense":
                sorted_df_armors = sorted_df_armors.sort_values(
                    by=['Defense', 'Decorations_score', 'Armor_type'], ascending=False)
            case "decorations":
                sorted_df_armors = sorted_df_armors.sort_values(
                    by=['Decorations_score', 'Defense', 'Armor_type'], ascending=False)

        df_best_armors = sorted_df_armors.groupby('Armor_type').apply(lambda x: x.iloc[0]).reset_index(drop=True)

        return df_best_armors

    def make_relevant_armor_sets(self, filtered_df_armors, filtered_df_talismans, df_best_armors):
        df_usable_armors = pd.concat([filtered_df_armors, df_best_armors])
        all_relevant_sets = []
        # Armors head loop
        for id, df_armor_head in df_usable_armors[df_usable_armors['Armor_type'] == 'head'].iterrows():
            armor_set_head = ArmorSet()
            armor_set_head.update_armors(armor_type='head', df_armors_filtered_by_type=df_armor_head)
            # Armors chest loop
            for id, df_armor_chest in df_usable_armors[df_usable_armors['Armor_type'] == 'chest'].iterrows():
                armor_set_chest = deepcopy(armor_set_head)
                armor_set_chest.update_armors(armor_type='chest', df_armors_filtered_by_type=df_armor_chest)
                # Armors arm loop
                for id, df_armor_arm in df_usable_armors[df_usable_armors['Armor_type'] == 'arm'].iterrows():
                    armor_set_arm = deepcopy(armor_set_chest)
                    armor_set_arm.update_armors(armor_type='arm', df_armors_filtered_by_type=df_armor_arm)
                    # Armors waist loop
                    for id, df_armor_waist in df_usable_armors[df_usable_armors['Armor_type'] == 'waist'].iterrows():
                        armor_set_waist = deepcopy(armor_set_arm)
                        armor_set_waist.update_armors(armor_type='waist', df_armors_filtered_by_type=df_armor_waist)
                        # Armors leg loop
                        for id, df_armor_leg in df_usable_armors[df_usable_armors['Armor_type'] == 'leg'].iterrows():
                            armor_set_leg = deepcopy(armor_set_waist)
                            armor_set_leg.update_armors(armor_type='leg', df_armors_filtered_by_type=df_armor_leg)
                            # Talismans loop
                            for id, df_talisman in filtered_df_talismans.iterrows():
                                armor_set_talisman = deepcopy(armor_set_leg)
                                armor_set_talisman.update_talisman(df_talisman)
                                # Append finished set
                                all_relevant_sets.append(armor_set_talisman)

        all_relevant_sets = pd.concat(
            [pd.json_normalize(relevant_set.__dict__, sep='_') for relevant_set in all_relevant_sets])
        return all_relevant_sets

    def get_best_set(self, all_relevant_sets, df_skills, necessary_skills, sort_on='defense'):
        all_relevant_sets.reset_index(inplace=True, drop=True)
        all_relevant_sets = all_relevant_sets.fillna(0)

        filter = True
        for skill_name in necessary_skills:
            filter &= (all_relevant_sets[f'skills_{skill_name}']
                       <= df_skills[df_skills['Skill'] == skill_name]['skill_max_level'].item())
        all_relevant_sets = all_relevant_sets.loc[filter].reset_index(drop=True)

        match sort_on:
            case "defense":
                sort_by = [f'skills_{skill_name}' for skill_name in necessary_skills]\
                    + ['defense', 'decorations_score', 'nb_decorations_size_1']
            case "decorations":
                sort_by = [f'skills_{skill_name}' for skill_name in necessary_skills]\
                    + ['decorations_score', 'defense', 'nb_decorations_size_1']
        best_set = all_relevant_sets.sort_values(by=sort_by, ascending=False).iloc[0].to_frame().transpose()

        best_set[best_set.columns[11:]] = best_set[best_set.columns[11:]].replace(0, np.nan)
        best_set.dropna(inplace=True, axis=1)

        return best_set
