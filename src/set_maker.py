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

    def _armor_set_recursion(self, i, armor_set, all_armor_sets, df_usable_armors, armor_cat, filtered_df_talismans):
        if i < 5:
            for id, armor in df_usable_armors[df_usable_armors['Armor_type'] == armor_cat[i]].iterrows():
                armor_set_part = deepcopy(armor_set)
                armor_set_part.update_armors(armor_type=armor_cat[i], df_armors_filtered_by_type=armor)
                all_armor_sets = self._armor_set_recursion(
                    i+1, armor_set_part, all_armor_sets, df_usable_armors, armor_cat, filtered_df_talismans)
        else:
            for id, talisman in filtered_df_talismans.iterrows():
                armor_set_talisman = deepcopy(armor_set)
                armor_set_talisman.update_talisman(talisman)
                all_armor_sets.append(armor_set_talisman)
        return all_armor_sets

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
        armor_cat = ['head', 'chest', 'arm', 'waist', 'leg']

        all_armor_sets = []
        armor_set = ArmorSet()

        all_armor_sets = self._armor_set_recursion(
            0, armor_set, all_armor_sets, df_usable_armors, armor_cat, filtered_df_talismans)

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
            pandas.DataFrame: All valid armor sets.
        """
        all_armor_sets.reset_index(inplace=True, drop=True)
        all_armor_sets = all_armor_sets.fillna(0)

        filter = True
        for skill_name in [col_skill for col_skill in all_armor_sets.columns if 'skills' in col_skill]:
            filter &= (all_armor_sets[skill_name]
                       <= df_skills[df_skills['Skill'] == skill_name.split('_')[1]]['skill_max_level'].item())
        all_relevant_sets = all_armor_sets.loc[filter].reset_index(drop=True)

        return all_relevant_sets

    def add_defense_by_skills_to_armor_sets(self, all_relevant_sets):
        """
        Adjusts the base defense value of each armor set based on defense-related skills.

        This method modifies the 'defense' column in the DataFrame by applying percentage-based
        and flat bonuses from active defensive skills such as:
        - Defense Boost (Lv1-Lv5)
        - Elemental Resistances (e.g., Fire, Ice, Dragon, Thunder, Water) at Lv3

        The skill impact is defined in a dictionary (`defense_by_skills`) where each key represents
        a skill at a specific level, and the corresponding value is a list:
        [percentage_bonus, flat_bonus].

        Args:
            all_relevant_sets (pandas.DataFrame): All valid armor sets.

        Returns:
            pandas.DataFrame: The same DataFrame with updated defense values reflecting skill-based bonuses.
        """
        defense_by_skills = {
            'Defense Boost_lv0': [0/100, 0],
            'Defense Boost_lv1': [0/100, 5],
            'Defense Boost_lv2': [0/100, 10],
            'Defense Boost_lv3': [5/100, 10],
            'Defense Boost_lv4': [5/100, 20],
            'Defense Boost_lv5': [8/100, 20],
            'Dragon Resistance_lv0': [0/100, 0],
            'Dragon Resistance_lv1': [0/100, 0],
            'Dragon Resistance_lv2': [0/100, 0],
            'Dragon Resistance_lv3': [0/100, 10],
            'Fire Resistance_lv0': [0/100, 0],
            'Fire Resistance_lv1': [0/100, 0],
            'Fire Resistance_lv2': [0/100, 0],
            'Fire Resistance_lv3': [0/100, 10],
            'Ice Resistance_lv0': [0/100, 0],
            'Ice Resistance_lv1': [0/100, 0],
            'Ice Resistance_lv2': [0/100, 0],
            'Ice Resistance_lv3': [0/100, 10],
            'Thunder Resistance_lv0': [0/100, 0],
            'Thunder Resistance_lv1': [0/100, 0],
            'Thunder Resistance_lv2': [0/100, 0],
            'Thunder Resistance_lv3': [0/100, 10],
            'Water Resistance_lv0': [0/100, 0],
            'Water Resistance_lv1': [0/100, 0],
            'Water Resistance_lv2': [0/100, 0],
            'Water Resistance_lv3': [0/100, 10]
        }

        cols_skills = [col_skill for col_skill in all_relevant_sets.columns if 'skills' in col_skill]
        defense_skill_names = [defense_skill.split('_')[0] for defense_skill in defense_by_skills.keys()]

        cols_defense_skills = [col_skill for col_skill in cols_skills if col_skill.split('_')[1] in defense_skill_names]
        cols_defense_skills.sort()

        for col_skill in cols_defense_skills:
            all_relevant_sets['defense'] = all_relevant_sets.apply(
                lambda x: x['defense']
                + (defense_by_skills[f'{col_skill.split('_')[1]}_lv{int(x[col_skill])}'][0] * x['defense'])
                + defense_by_skills[f'{col_skill.split('_')[1]}_lv{int(x[col_skill])}'][1],
                axis=1
                )

        all_relevant_sets['defense'] = all_relevant_sets['defense'].round().astype(int)

        return all_relevant_sets

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
