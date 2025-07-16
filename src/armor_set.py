import numpy as np


class ArmorSet:
    def __init__(self):
        self.head = ''
        self.chest = ''
        self.arm = ''
        self.waist = ''
        self.leg = ''
        self.talisman = ''
        self.defense = 0
        self.skills = {}
        self.nb_decorations_size_1 = 0
        self.nb_decorations_size_2 = 0
        self.nb_decorations_size_3 = 0
        self.decorations_score = 0

    def _update_armor_name_based_on_type(self, armor_type, df_armors_filtered_by_type):
        match armor_type:
            case 'head':
                self.head = df_armors_filtered_by_type['Armor']
            case 'chest':
                self.chest = df_armors_filtered_by_type['Armor']
            case 'arm':
                self.arm = df_armors_filtered_by_type['Armor']
            case 'waist':
                self.waist = df_armors_filtered_by_type['Armor']
            case 'leg':
                self.leg = df_armors_filtered_by_type['Armor']

    def update_armors(self, armor_type, df_armors_filtered_by_type):
        self._update_armor_name_based_on_type(armor_type, df_armors_filtered_by_type)
        self.defense += df_armors_filtered_by_type['Defense']

        skills_cols_names = ['Skill_1', 'Skill_2', 'Skill_3']
        for col in skills_cols_names:
            if df_armors_filtered_by_type[f'{col}_name'] is not np.nan:
                if df_armors_filtered_by_type[f'{col}_name'] not in self.skills:
                    self.skills[df_armors_filtered_by_type[f'{col}_name']] = df_armors_filtered_by_type[f'{col}_lvl']
                else:
                    self.skills[df_armors_filtered_by_type[f'{col}_name']] += df_armors_filtered_by_type[f'{col}_lvl']

        decoration_cols_names = ['Decoration_slot_1_size', 'Decoration_slot_2_size', 'Decoration_slot_3_size']
        for col in decoration_cols_names:
            match df_armors_filtered_by_type[col]:
                case 1:
                    self.nb_decorations_size_1 += 1
                case 2:
                    self.nb_decorations_size_2 += 1
                case 3:
                    self.nb_decorations_size_3 += 1

        self.decorations_score += df_armors_filtered_by_type['Decorations_score']

    def update_talisman(self, df_talismans):
        self.talisman = df_talismans['Talisman']
        if df_talismans['Skill_name'] not in self.skills:
            self.skills[df_talismans['Skill_name']] = df_talismans['Skill_lvl']
        else:
            self.skills[df_talismans['Skill_name']] += df_talismans['Skill_lvl']
