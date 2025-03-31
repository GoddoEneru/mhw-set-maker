import requests
from bs4 import BeautifulSoup
import pandas as pd


def decorations_scraper(url, num_table, name_csv):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    table = soup.find_all('table')

    columns = [i.get_text(strip=True) for i in table[num_table].find_all("th")]
    data = []

    for tr in table[num_table].find("tbody").find_all("tr"):
        data.append([td.get_text(strip=True) for td in tr.find_all("td")])

    df_decorations = pd.DataFrame(data, columns=columns)

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

    df_decorations.to_csv(name_csv, index=False)
