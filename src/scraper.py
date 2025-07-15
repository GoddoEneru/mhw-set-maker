import requests
from bs4 import BeautifulSoup
import pandas as pd


class Scraper:
    def __init__(
            self,
            decoration_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500473",
            decoration_csv="src/data/decorations.csv",
            head_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500636",
            chest_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500639",
            arm_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500640",
            waist_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500641",
            leg_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500642",
            armors_by_monster_low_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500342",
            armors_by_monster_high_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500343",
            armors_csv="src/data/armors.csv",
            skills_info_url="https://game8.co/games/Monster-Hunter-Wilds/archives/482545",
            skills_info_csv="src/data/skills.csv",
            talismans_url="https://game8.co/games/Monster-Hunter-Wilds/archives/497353",
            talismans_csv="src/data/talismans.csv"
            ):
        self.decoration_url = decoration_url
        self.decoration_csv = decoration_csv
        self.head_armors_url = head_armors_url
        self.chest_armors_url = chest_armors_url
        self.arm_armors_url = arm_armors_url
        self.waist_armors_url = waist_armors_url
        self.leg_armors_url = leg_armors_url
        self.armors_by_monster_low_url = armors_by_monster_low_url
        self.armors_by_monster_high_url = armors_by_monster_high_url
        self.armors_csv = armors_csv
        self.skills_info_url = skills_info_url
        self.skills_info_csv = skills_info_csv
        self.talismans_url = talismans_url
        self.talismans_csv = talismans_csv

    def _get_table_from_url(self, url, text):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all('table')
        for table in tables:
            if len(table.find_all('th', text=text)) >= 1:
                return table

    def _get_one_col_per_skill(self, df, skills_col_name, reg_rule):
        temp = df[skills_col_name].str.extractall(reg_rule).unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={i: f'Skill {i+1}' for i in temp.columns}, inplace=True)
        return df

    def _get_skill_lvl_from_skill_columns(self, df, n):
        temp = df[f'Skill {n}'].str.extractall(r'(\d)').unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={0: f"Skill_{n}_lvl"}, inplace=True)
        return df

    def _slot_size_char_to_int(self, c):
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
        if skill[-1].isnumeric():
            return skill
        return skill + "1"

    def decorations_scraping(self):
        table = self._get_table_from_url(self.decoration_url, "Slots")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_decorations = pd.DataFrame(data, columns=columns)

        df_decorations = self._get_one_col_per_skill(df_decorations, 'Skill', r'(\D+Lv. \d)')
        for n in range(1, 2):
            temp = df_decorations[f'Skill {n}'].str.split(r'(Lv. \d)').str[0]
            df_decorations[f"Skill_{n}_name"] = temp
            df_decorations = self._get_skill_lvl_from_skill_columns(df_decorations, n)

        df_decorations.drop(columns=[
            'Skill',
            'Skill 1',
            ], inplace=True)

        df_decorations.rename(columns={"Decoration": "Decoration_name", "Slots": "Decoration_size"}, inplace=True)

        df_decorations.to_csv(self.decoration_csv, index=False)
        print("Decoration data scraping done !")

    def armors_scraping(self):
        # get data from armors by type (head, chest, arm, waist and leg)
        df_armors = pd.DataFrame()
        armors_by_type_urls = [
            self.head_armors_url,
            self.chest_armors_url,
            self.arm_armors_url,
            self.waist_armors_url,
            self.leg_armors_url
            ]

        armor_types = ["head", "chest", "arm", "waist", "leg"]

        for i, url in enumerate(armors_by_type_urls):
            table = self._get_table_from_url(url, "Armor")
            columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
            columns.append("Armor_type")
            data = []

            for tr in table.find("tbody").find_all("tr"):
                row = [td.get_text(strip=True) for td in tr.find_all("td")]
                row.append(armor_types[i])
                data.append(row)
            df_armors = pd.concat([df_armors, pd.DataFrame(data, columns=columns)])

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

        # get decorations slots from armors by monster
        df_decorations_slots = pd.DataFrame()

        armors_decorations_slots_links = []
        for armors_by_monster_url in [self.armors_by_monster_low_url, self.armors_by_monster_high_url]:
            table = self._get_table_from_url(armors_by_monster_url, "Skills")
            anchors = [tr.find("a") for tr in table.find("tbody").find_all("tr")]
            armors_decorations_slots_links += [a.get('href') for a in anchors]

        for link in armors_decorations_slots_links:
            try:
                table = self._get_table_from_url(link, "Slots")
                columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
                data = []

                for tr in table.find_all("tr"):
                    data.append([td.get_text(strip=True) for td in tr.find_all("td")])
                df_decorations_slots = pd.concat([df_decorations_slots, pd.DataFrame(data, columns=columns)])
            except Exception as e:
                print(e)
                print(link)
                print("".join(['-' for i in range(50)]))

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
        print("Armors data scraping done !")

    def skills_info_scraping(self):
        table = self._get_table_from_url(self.skills_info_url, "Type")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_skills_info = pd.DataFrame(data, columns=columns)

        temp = df_skills_info['Effect'].str.extractall(r'(Lv. \d)').unstack()
        temp.columns = temp.columns.droplevel()
        temp['final'] = temp.ffill(axis=1).iloc[:, -1]
        temp['final'] = temp['final'].str.extract(r'(\d)')
        df_skills_info['skill_max_level'] = temp['final']

        df_skills_info = df_skills_info[df_skills_info['Type'] == 'Armor'].reset_index(drop=True)

        df_skills_info.to_csv(self.skills_info_csv, index=False)
        print("Skills info data scraping done !")

    def talismans_scraping(self):
        table = self._get_table_from_url(self.talismans_url, "Talisman")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_talismans = pd.DataFrame(data, columns=columns)

        df_talismans["Skill_name"] = df_talismans['Skill'].str.split(r'(Lv \d)').str[0]
        df_talismans["Skill_lvl"] = df_talismans['Skill'].str.extract(r'(\d)')
        df_talismans.drop(columns=['Skill'], inplace=True)

        df_talismans.to_csv(self.talismans_csv, index=False)
        print("talismans data scraping done !")
