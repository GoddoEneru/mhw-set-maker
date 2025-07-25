import pandas as pd
import numpy as np
from copy import deepcopy

from src.armor_set import ArmorSet


class SetMaker:
    """
    A class responsible for generating optimized armor sets based on user-defined skill preferences.

    This class loads cleaned armor, talisman, and skill data, filters relevant items,
    computes combinations of armor sets, and returns valid or optimal configurations
    based on defense or decoration potential.
    """
    def __init__(self):
        self.df_armors = pd.read_csv("src/data/armors.csv")
        self.df_talismans = pd.read_csv("src/data/talismans.csv")
        self.df_skills = pd.read_csv("src/data/skills.csv")

    def add_decorations_score_col(self, df_armors):
        """
        Adds a 'Decorations_score' column to the armor DataFrame by summing
        the sizes of all available decoration slots.

        Args:
            df_armors (pandas.DataFrame): The armor data.

        Returns:
            pandas.DataFrame: The modified armor DataFrame with a new 'Decorations_score' column.
        """
        decoration_cols_names = ['Decoration_slot_1_size', 'Decoration_slot_2_size', 'Decoration_slot_3_size']
        df_armors[decoration_cols_names] = df_armors[decoration_cols_names].fillna(0)
        df_armors['Decorations_score'] = df_armors.apply(
            lambda x: x['Decoration_slot_1_size'] + x['Decoration_slot_2_size'] + x['Decoration_slot_3_size'], axis=1)
        return df_armors

    def filter_relevant_armors_and_talismans(self, skills, df_armors, df_talismans):
        """
        Filters armors and talismans to only include those with the desired skills.

        - Filters armors that provide any of the desired skills.
        - Filters and reduces talismans to one per skill with the highest level.

        Args:
            skills (list): List of skill names to search for.
            df_armors (pandas.DataFrame): Armor data.
            df_talismans (pandas.DataFrame): Talisman data.

        Returns:
            tuple:
                - pandas.DataFrame: Filtered armors.
                - pandas.DataFrame: Filtered talismans.
        """
        filter = df_armors['Skill_1_name'].isin(skills)\
            | df_armors['Skill_2_name'].isin(skills)\
            | df_armors['Skill_3_name'].isin(skills)
        filtered_df_armors = df_armors.loc[filter]

        skills = skills + ['Defense Boost']
        filter = df_talismans['Skill_name'].isin(skills)
        filtered_df_talismans = df_talismans.loc[filter]
        filtered_df_talismans = filtered_df_talismans.sort_values(by=['Skill_lvl'], ascending=False)
        filtered_df_talismans = filtered_df_talismans.groupby('Skill_name').apply(
            lambda x: x.iloc[0]).reset_index(drop=True)

        return filtered_df_armors, filtered_df_talismans

    def get_best_armor_for_each_type(self, df_armors, sort_on='defense'):
        """
        Retrieves the top-performing armor piece for each type (head, chest, etc.)
        based on the given sorting criteria.

        Args:
            df_armors (pandas.DataFrame): DataFrame of available armors.
            sort_on (str): Criteria to sort by; either 'defense' or 'decorations'.

        Returns:
            pandas.DataFrame: The best armor piece for each armor type.
        """
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

    def make_armor_sets(self, filtered_df_armors, filtered_df_talismans, df_best_armors):
        """
        Generates all possible combinations of armor sets by iterating over every
        valid combination of armor pieces and talismans.

        - Uses deep copies to preserve intermediate state.
        - Builds full sets (head, chest, arm, waist, leg + talisman).

        Args:
            filtered_df_armors (pandas.DataFrame): Filtered set of relevant armors.
            filtered_df_talismans (pandas.DataFrame): Filtered set of relevant talismans.
            df_best_armors (pandas.DataFrame): Best armor pieces by type to supplement combinations.

        Returns:
            pandas.DataFrame: All generated armor set combinations.
        """
        df_usable_armors = pd.concat([filtered_df_armors, df_best_armors])
        all_armor_sets = []
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
                                all_armor_sets.append(armor_set_talisman)

        if len(all_armor_sets) > 1:
            all_armor_sets = pd.concat(
                [pd.json_normalize(armor_set.__dict__, sep='_') for armor_set in all_armor_sets])
        elif len(all_armor_sets) == 1:
            all_armor_sets = pd.json_normalize(all_armor_sets[0].__dict__, sep='_')
        return all_armor_sets

    def filter_valid_armor_sets(self, all_armor_sets, df_skills):
        """
        Filters out armor sets that exceed the maximum allowed skill levels.

        - Compares each skill in the armor set against its max level.
        - Keeps only the valid combinations.

        Args:
            all_armor_sets (pandas.DataFrame): All generated armor sets.
            df_skills (pandas.DataFrame): Skill data containing max level for each skill.

        Returns:
            pandas.DataFrame: Valid armor sets.
        """
        all_armor_sets.reset_index(inplace=True, drop=True)
        all_armor_sets = all_armor_sets.fillna(0)

        filter = True
        for skill_name in [col_skill for col_skill in all_armor_sets.columns if 'skills' in col_skill]:
            filter &= (all_armor_sets[skill_name]
                       <= df_skills[df_skills['Skill'] == skill_name.split('_')[1]]['skill_max_level'].item())
        all_relevant_sets = all_armor_sets.loc[filter].reset_index(drop=True)

        return all_relevant_sets

    # add_defense_by_skills_to_armor_sets(self, all_relevant_sets)

    def get_best_set(self, all_relevant_sets, necessary_skills, sort_on='defense'):
        """
        Selects the best armor set among all valid ones, based on required skills
        and a prioritization criterion (defense or decoration score).

        - Sorts by skill levels, defense, decoration score, and slot availability.
        - Drops unused columns and empty skill entries.

        Args:
            all_relevant_sets (pandas.DataFrame): Valid armor sets.
            necessary_skills (list): Skills required in the final armor set.
            sort_on (str): Primary sorting criterion, 'defense' or 'decorations'.

        Returns:
            pandas.DataFrame: A single-row DataFrame containing the best armor set.
        """
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
