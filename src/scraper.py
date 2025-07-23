import requests
from bs4 import BeautifulSoup
import pandas as pd


class Scraper:
    """
    A web scraping class for extracting Monster Hunter game data from Game8.co pages.

    This class retrieves tables containing information about decorations, armors,
    skills, and talismans from various pre-defined URLs. The resulting data is returned
    as pandas DataFrames ready for further processing.
    """
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
        """
        Retrieves the first HTML table from a given URL that contains a specific column header.

        Args:
            url (str): The webpage URL to scrape.
            text (str): Text content to match in one of the table headers (e.g., 'Slots').

        Returns:
            bs4.element.Tag: The BeautifulSoup table tag if found, otherwise None.
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all('table')
        for table in tables:
            if len(table.find_all('th', text=text)) >= 1:
                return table

    def decorations_scraping(self):
        """
        Scrapes the decorations table from the decoration URL.

        - Extracts columns such as skill and slot size from the table.
        - Converts the raw HTML data into a pandas DataFrame.

        Returns:
            pandas.DataFrame: A DataFrame containing decoration data.
        """
        table = self._get_table_from_url(self.decoration_url, "Slots")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_decorations = pd.DataFrame(data, columns=columns)
        return df_decorations

    def armors_scraping(self):
        """
        Scrapes armor data from multiple armor-type URLs and retrieves decoration slot info from monster-specific pages.

        - Merges armor pieces of different types into a unified DataFrame.
        - Collects slot sizes by scraping linked monster-specific armor pages.
        - Converts the raw HTML data into two pandas DataFrame.

        Returns:
            tuple:
                - pandas.DataFrame: Armor data with type labels.
                - pandas.DataFrame: Decoration slot information per armor piece.
        """
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
        """
        Scrapes the skills information table from the skills info URL.

        - Extracts details such as skill names, types, and effect descriptions.
        - Converts the raw HTML data into a pandas DataFrame.

        Returns:
            pandas.DataFrame: A DataFrame containing skill names, effects, and related metadata.
        """
        table = self._get_table_from_url(self.skills_info_url, "Type")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_skills_info = pd.DataFrame(data, columns=columns)
        return df_skills_info

    def talismans_scraping(self):
        """
        Scrapes the talismans table from the talismans URL.

        - Extracts talisman names, skills, and slot information.
        - Converts the raw HTML data into a pandas DataFrame.

        Returns:
            pandas.DataFrame: A DataFrame containing talisman information.
        """
        table = self._get_table_from_url(self.talismans_url, "Talisman")
        columns = [col_name.get_text(strip=True) for col_name in table.find_all("th")]
        data = []

        for tr in table.find("tbody").find_all("tr"):
            data.append([td.get_text(strip=True) for td in tr.find_all("td")])
        df_talismans = pd.DataFrame(data, columns=columns)
        return df_talismans
