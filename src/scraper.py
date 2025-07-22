import requests
from bs4 import BeautifulSoup
import pandas as pd


class Scraper:
    def __init__(
            self,
            decoration_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500473",
            head_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500636",
            chest_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500639",
            arm_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500640",
            waist_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500641",
            leg_armors_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500642",
            armors_by_monster_low_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500342",
            armors_by_monster_high_url="https://game8.co/games/Monster-Hunter-Wilds/archives/500343",
            skills_info_url="https://game8.co/games/Monster-Hunter-Wilds/archives/482545",
            talismans_url="https://game8.co/games/Monster-Hunter-Wilds/archives/497353",
            ):
        self.decoration_url = decoration_url
        self.head_armors_url = head_armors_url
        self.chest_armors_url = chest_armors_url
        self.arm_armors_url = arm_armors_url
        self.waist_armors_url = waist_armors_url
        self.leg_armors_url = leg_armors_url
        self.armors_by_monster_low_url = armors_by_monster_low_url
        self.armors_by_monster_high_url = armors_by_monster_high_url
        self.skills_info_url = skills_info_url
        self.talismans_url = talismans_url

    def _get_table_from_url(self, url, text):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all('table')
        for table in tables:
            if len(table.find_all('th', text=text)) >= 1:
                return table

    def decorations_scraping(self):
        table = self._get_table_from_url(self.decoration_url, "Slots")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_decorations = pd.DataFrame(data, columns=columns)
        return df_decorations

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

        return df_armors, df_decorations_slots

    def skills_info_scraping(self):
        table = self._get_table_from_url(self.skills_info_url, "Type")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_skills_info = pd.DataFrame(data, columns=columns)
        return df_skills_info

    def talismans_scraping(self):
        table = self._get_table_from_url(self.talismans_url, "Talisman")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_talismans = pd.DataFrame(data, columns=columns)
        return df_talismans
