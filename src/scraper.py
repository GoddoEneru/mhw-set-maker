import requests
from bs4 import BeautifulSoup
import pandas as pd


class Scraper:
    def __init__(
            self,
            decoration_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500473",
            decoration_table_num=1,
            decoration_csv="src/data/decorations.csv",
            head_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500636",
            chest_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500639",
            arm_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500640",
            waist_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500641",
            leg_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500642",
            armors_by_type_num=1,
            armors_by_monster_url="https://game8.co/games/Monster-Hunter-Wilds/archives/482808",
            armors_by_monster_table_num=1,
            ):
        self.decoration_url = decoration_url
        self.decoration_table_num = decoration_table_num
        self.decoration_csv = decoration_csv
        self.head_armors_url = head_armors_url
        self.chest_armors_url = chest_armors_url
        self.arm_armors_url = arm_armors_url
        self.waist_armors_url = waist_armors_url
        self.leg_armors_url = leg_armors_url
        self.armors_by_type_num = armors_by_type_num
        self.armors_by_monster_url = armors_by_monster_url
        self.armors_by_monster_table_num = armors_by_monster_table_num

    def get_tables_from_url(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all('table')
        return tables

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
        tables = self.get_tables_from_url(self.decoration_url)
        columns = [i.get_text(strip=True) for i in tables[self.decoration_table_num].find_all("th")]
        data = []

        for tr in tables[self.decoration_table_num].find("tbody").find_all("tr"):
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
            tables = self.get_tables_from_url(url)
            columns = [i.get_text(strip=True) for i in tables[self.armors_by_type_num].find_all("th")]
            data = []

            for tr in tables[self.armors_by_type_num].find("tbody").find_all("tr"):
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
        tables = self.get_tables_from_url(self.armors_by_monster_url)
        armors_decorations_slots_links = tables[self.armors_by_monster_table_num].find_all("a")
        armors_decorations_slots_links = [a.get('href') for a in armors_decorations_slots_links]

        for link in armors_decorations_slots_links:
            tables = self.get_tables_from_url(link)
            print(tables)
            break

        # TODO: concat decorations slots data from each monster's armor page

        # TODO: add decorations slots data to df_armors and save df_armors
