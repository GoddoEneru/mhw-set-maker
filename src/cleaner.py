import pandas as pd


class Cleaner:
    """
    A data cleaning class for processing raw data related to decorations,
    armors, skills, and talismans. This class prepares and saves structured, cleaned datasets
    for further analysis or machine learning tasks.
    """
    def __init__(
            self,
            decoration_csv="src/data/decorations.csv",
            armors_csv="src/data/armors.csv",
            skills_info_csv="src/data/skills.csv",
            talismans_csv="src/data/talismans.csv"
            ):
        self.decoration_csv = decoration_csv
        self.armors_csv = armors_csv
        self.skills_info_csv = skills_info_csv
        self.talismans_csv = talismans_csv

    def _get_one_col_per_skill(self, df, skills_col_name, reg_rule):
        """
        Extracts individual skill entries from a single string column using a regex pattern,
        and expands them into separate columns.

        Args:
            df (pandas.DataFrame): The input DataFrame containing the skills column.
            skills_col_name (str): Name of the column containing skills data.
            reg_rule (str): Regular expression rule used to extract each skill.

        Returns:
            pandas.DataFrame: The updated DataFrame with each skill in its own column.
        """
        temp = df[skills_col_name].str.extractall(reg_rule).unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={i: f'Skill {i+1}' for i in temp.columns}, inplace=True)
        return df

    def _get_skill_lvl_from_skill_columns(self, df, n):
        """
        Extracts the numerical skill level from the nth skill column and adds it as a new column.

        Args:
            df (pandas.DataFrame): The DataFrame containing skill columns.
            n (int): The skill number (e.g., 1 for 'Skill 1') to process.

        Returns:
            pandas.DataFrame: The DataFrame with an added column for the skill level
        """
        temp = df[f'Skill {n}'].str.extractall(r'(\d)').unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={0: f"Skill_{n}_lvl"}, inplace=True)
        return df

    def _slot_size_char_to_int(self, c):
        """
        Converts a symbolic representation of slot size to an integer.

        Args:
            c (str): A character representing slot size (e.g., '①', '②', '③', 'ー').

        Returns:
            int or None: Integer slot size (1-3) or None if no slot is present.
        """
        match c:
            case "ー":
                return None
            case "①":
                return 1
            case "②":
                return 2
            case "③":
                return 3

    def _correct_error_in_skill_col(self, skill):
        """
        Ensures skill strings end with a numerical level. If not, appends a default level of '1'.

        Args:
            skill (str): The raw skill string.

        Returns:
            str: Corrected skill string ending with a digit.
        """
        if skill[-1].isnumeric():
            return skill
        return skill + "1"

    def decorations_cleaning(self, df_decorations):
        """
        Cleans and restructures the decorations dataset.

        - Splits combined skill data into individual columns.
        - Extracts skill name and level from each skill column.
        - Renames and formats relevant columns.
        - Outputs a cleaned CSV file to `self.decoration_csv`.

        Args:
            df_decorations (pandas.DataFrame): Raw decorations data.
        """
        df_decorations = self._get_one_col_per_skill(df_decorations, 'Skill', r'(\D+Lv. \d)')
        for n in range(1, 2):
            temp = df_decorations[f'Skill {n}'].str.split(r'(Lv. \d)').str[0]
            df_decorations[f"Skill_{n}_name"] = temp
            df_decorations = self._get_skill_lvl_from_skill_columns(df_decorations, n)

        df_decorations.drop(columns=['Skill', 'Skill 1'], inplace=True)
        df_decorations.rename(columns={"Decoration": "Decoration_name", "Slots": "Decoration_size"}, inplace=True)

        df_decorations.to_csv(self.decoration_csv, index=False)

    def armors_cleaning(self, df_armors, df_decorations_slots):
        """
        Cleans and restructures the armors dataset and merges decorations slots information to it.

        - Extracts defense values and corrects skill column inconsistencies.
        - Parses skill names and levels into structured columns.
        - Extracts and converts decoration slot sizes from symbols to integers.
        - Merges armor data with slot information using the 'Armor' column.
        - Normalizes special characters in armor names.
        - Outputs a cleaned CSV file to `self.armors_csv`.

        Args:
            df_armors (pandas.DataFrame): Raw armor data.
            df_decorations_slots (pandas.DataFrame): Decoration slot data associated with each armor.
        """
        df_armors.reset_index(drop=True, inplace=True)

        df_armors.rename(columns={"": "Defense"}, inplace=True)
        df_armors["Defense"] = df_armors["Defense"].str.findall(r'\d+').str[0]

        df_armors = self._get_one_col_per_skill(df_armors, 'Skills', r'(\D+\d*)')
        for n in range(1, 4):
            df_armors[f'Skill {n}'] = df_armors[f'Skill {n}'].apply(
                lambda x: x if pd.isnull(x) else self._correct_error_in_skill_col(x)
                )
            df_armors[f"Skill_{n}_name"] = df_armors[f'Skill {n}'].str[:-1]
            df_armors = self._get_skill_lvl_from_skill_columns(df_armors, n)

        df_armors.drop(columns=[
            'Type 1',
            'Type 2',
            'Resistances',
            'Skills',
            'Skill 1',
            'Skill 2',
            'Skill 3',
            ], inplace=True)

        df_decorations_slots = df_decorations_slots[~df_decorations_slots["Armor"].isna()]

        df_slots_size = pd.DataFrame([list(x) for x in df_decorations_slots['Slots']], index=df_decorations_slots.index)
        slots_size_col_names = ["Decoration_slot_1_size", "Decoration_slot_2_size", "Decoration_slot_3_size"]
        df_slots_size.columns = slots_size_col_names

        df_decorations_slots = pd.concat([df_decorations_slots, df_slots_size], axis=1)

        for col in slots_size_col_names:
            df_decorations_slots[col] = df_decorations_slots[col].apply(lambda x: self._slot_size_char_to_int(x))

        df_armors = df_armors.merge(df_decorations_slots, how='inner', on='Armor')

        for k, v in {"α": "alpha", "β": "beta", "γ": "upsilon"}.items():
            df_armors['Armor'] = df_armors['Armor'].str.replace(k, v)

        df_armors.drop(columns=[
            'Set',
            'Slots',
            'Skills'
            ], inplace=True)

        df_armors.to_csv(self.armors_csv, index=False)

    def skills_info_cleaning(self, df_skills_info):
        """
        Cleans the skills information dataset by extracting max skill levels.

        - Parses the 'Effect' column to determine the maximum skill level per skill.
        - Filters to keep only skills of type 'Armor'.
        - Outputs a cleaned CSV file to `self.skills_info_csv`.

        Args:
            df_skills_info (pandas.DataFrame): Raw skill details and effects.
        """
        temp = df_skills_info['Effect'].str.extractall(r'(Lv. \d)').unstack()
        temp.columns = temp.columns.droplevel()
        temp['final'] = temp.ffill(axis=1).iloc[:, -1]
        temp['final'] = temp['final'].str.extract(r'(\d)')
        df_skills_info['skill_max_level'] = temp['final']

        df_skills_info = df_skills_info[df_skills_info['Type'] == 'Armor'].reset_index(drop=True)

        df_skills_info.to_csv(self.skills_info_csv, index=False)

    def talismans_cleaning(self, df_talismans):
        """
        Cleans the talismans dataset by separating skill name and level.

        - Extracts the skill name and numeric level from the 'Skill' column.
        - Drops redundant or merged columns.
        - Outputs a cleaned CSV file to `self.talismans_csv`.

        Args:
            df_talismans (pandas.DataFrame): Raw talisman data.
        """
        df_talismans["Skill_name"] = df_talismans['Skill'].str.split(r'(Lv \d)').str[0]
        df_talismans["Skill_lvl"] = df_talismans['Skill'].str.extract(r'(\d)')
        df_talismans.drop(columns=['Skill'], inplace=True)

        df_talismans.to_csv(self.talismans_csv, index=False)
