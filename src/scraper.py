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

    def get_table_from_url(self, url, text):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all('table')
        for table in tables:
            if len(table.find_all('th', text=text)) >= 1:
                return table

    def get_one_col_per_skill(self, df, skills_col_name, reg_rule):
        temp = df[skills_col_name].str.extractall(reg_rule).unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={i: f'Skill {i+1}' for i in temp.columns}, inplace=True)
        return df

    def get_skill_lvl_from_skill_columns(self, df, n):
        temp = df[f'Skill {n}'].str.extractall(r'(\d)').unstack()
        temp.columns = temp.columns.droplevel()
        df = pd.concat([df, temp], axis=1)
        df.rename(columns={0: f"Skill_{n}_lvl"}, inplace=True)
        return df

    def decorations_scraping(self):
        table = self.get_table_from_url(self.decoration_url, "Slots")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_decorations = pd.DataFrame(data, columns=columns)

        df_decorations = self.get_one_col_per_skill(df_decorations, 'Skill', r'(\D+Lv. \d)')
        for n in range(1, 2):
            temp = df_decorations[f'Skill {n}'].str.split(r'(Lv. \d)').str[0]
            df_decorations[f"Skill_{n}_name"] = temp
            df_decorations = self.get_skill_lvl_from_skill_columns(df_decorations, n)

        df_decorations.drop(columns=[
            'Skill',
            'Skill 1',
            ], inplace=True)

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

        for url in armors_by_type_urls:
            table = self.get_table_from_url(url, "Armor")
            columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
            data = []

            for tr in table.find("tbody").find_all("tr"):
                data.append([td.get_text(strip=True) for td in tr.find_all("td")])
            df_armors = pd.concat([df_armors, pd.DataFrame(data, columns=columns)])

        df_armors.reset_index(drop=True, inplace=True)

        df_armors.rename(columns={"": "Defense"}, inplace=True)
        df_armors["Defense"] = df_armors["Defense"].str.findall(r'\d').str.join("")

        df_armors = self.get_one_col_per_skill(df_armors, 'Skills', r'(\D+\d*)')
        for n in range(1, 4):
            df_armors[f"Skill_{n}_name"] = df_armors[f'Skill {n}'].str[:-1]
            df_armors = self.get_skill_lvl_from_skill_columns(df_armors, n)

        df_armors.drop(columns=[
            'Type 1',
            'Type 2',
            'Resistances',
            'Skills',
            'Skill 1',
            'Skill 2',
            'Skill 3'
            ], inplace=True)

        # get decorations slots from armors by monster
        df_decorations_slots = pd.DataFrame()

        armors_decorations_slots_links = []
        for armors_by_monster_url in [self.armors_by_monster_low_url, self.armors_by_monster_high_url]:
            table = self.get_table_from_url(armors_by_monster_url, "Skills")
            temp = [tr.find("a") for tr in table.find("tbody").find_all("tr")]
            armors_decorations_slots_links += [a.get('href') for a in temp]

        for link in armors_decorations_slots_links:
            try:
                table = self.get_table_from_url(link, "Slots")
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

        return df_decorations_slots, df_armors

        # TODO: add decorations slots data to df_armors and save df_armors

        return df_armors
