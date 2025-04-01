import requests
from bs4 import BeautifulSoup
import pandas as pd


class Scraper:
    def __init__(
            self,
            decoration_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500473",
            decoration_table_num=1,
            decoration_csv="src/data/decorations.csv"
            ):
        self.decoration_url = decoration_url
        self.decoration_table_num = decoration_table_num
        self.decoration_csv = decoration_csv

    def get_data(self, url, table_num):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        table = soup.find_all('table')

        columns = [i.get_text(strip=True) for i in table[table_num].find_all("th")]
        data = []

        for tr in table[table_num].find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])

        return pd.DataFrame(data, columns=columns)

    def decorations_scraping(self):
        df_decorations = self.get_data(self.decoration_url, self.decoration_table_num)
        temp = df_decorations['Skill'].str.extractall(r'(\D+Lv. \d)').unstack()
        temp.columns = temp.columns.droplevel()
        # temp.drop(columns=[2], inplace=True)

        df_decorations = pd.concat([df_decorations, temp], axis=1)
        df_decorations.rename(columns={0: "Skill 1", 1: "Skill 2"}, inplace=True)

        for n in range(1, 2):
            temp = df_decorations[f'Skill {n}'].str.split(r'(Lv. \d)').str[0]
            df_decorations[f"Skill_{n}_name"] = temp

            temp = df_decorations[f'Skill {n}'].str.extractall(r'(\d)').unstack()
            temp.columns = temp.columns.droplevel()
            df_decorations = pd.concat([df_decorations, temp], axis=1)
            df_decorations.rename(columns={0: f"Skill_{n}_lvl"}, inplace=True)

        df_decorations.drop(columns=[
            'Skill',
            'Skill 1',
            # 'Skill 2'
            ], inplace=True)

        df_decorations.to_csv(self.decoration_csv, index=False)
        print("Decoration data scraping done !")
