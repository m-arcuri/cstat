from typing import List
from dataclasses import dataclass
import sys
from math import ceil

import pandas as pd

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait


@dataclass
class PlayerCstat:
    name: str
    total_time: str
    human_time: str
    zombie_time: str
    zombie_kills: int
    zombie_hs: int
    infected: int
    items_picked: int
    boss_killed: int
    leader_count: int
    td_count: int

    def __init__(self, raw_text: List[str]):
        for line in raw_text:
            parts = line.split(":", 1)

            if len(parts) != 2:
                print(line, "does not fit expected format")
                raise Exception

            if parts[0] == "cStat Details":
                self.name = parts[1]
            elif parts[0] == "Total Time":
                self.total_time = parts[1]
            elif parts[0] == "Human Time":
                self.human_time = parts[1]
            elif parts[0] == "Zombie Time":
                self.zombie_time = parts[1]
            elif parts[0] == "Zombies Killed":
                self.zombie_kills = int(parts[1])
            elif parts[0] == "Zombies Killed (HS)":
                self.zombie_hs = int(parts[1])
            elif parts[0] == "Infected":
                self.infected = int(parts[1].rstrip(" players"))
            elif parts[0] == "Items picked up":
                self.items_picked = int(parts[1])
            elif parts[0] == "Boss Killed":
                self.boss_killed = int(parts[1])
            elif parts[0] == "Leader Count":
                self.leader_count = int(parts[1])
            elif parts[0] == "TopDefender Count":
                self.td_count = int(parts[1])
            else:
                print(parts[0], "does not match a case")
                raise Exception


def main():
    try:
        pages = round_pages(sys.argv[1])
    except (ValueError, IndexError):
        print("invalid input")
        exit(-1)

    print("Collecting", pages, "page(s) of cstat data...")
    raw_cstat_entries = scrape_text(pages)
    df = raw_extract_to_dataframe(raw_cstat_entries)
    df.to_excel("cstat.xlsx", index=False)
    print("Done.")
    exit(0)


def round_pages(arg: str) -> int:
    count = ceil(int(arg) / 15.0)
    if count < 0:
        raise ValueError
    return count


def scrape_text(pages: int) -> List[List[str]]:
    options = Options()
    options.binary = FirefoxBinary("/snap/bin/firefox")
    driver = webdriver.Firefox(options=options)

    url = "https://cstat.snowy.gg/?sort=totaltime"
    wait = WebDriverWait(driver, 10.0, 0.5)

    driver.get(url)

    cstat: List[List[str]] = []
    #INFO: PAGE ACTION BEGIN
    for i in range(0, pages):
        # Collect all cstat entries on page, should be 15, also remove the first header row
        clickable_table_rows: List[WebElement] = wait.until(lambda d: driver.find_elements(By.CSS_SELECTOR, "tr"))
        clickable_table_rows.pop(0)

        for row in clickable_table_rows:
            row.find_element(By.CSS_SELECTOR, "td").click()

        tables = driver.find_elements(By.CLASS_NAME, "table-opener")
        
        for table in tables:
            entry: List[str] = []
            for e in table.find_elements(By.CSS_SELECTOR, "tr"):
                entry.append(e.text)

            cstat.append(entry)

        
        if i < pages - 1:
            next_page_button: WebElement = wait.until(lambda d: driver.find_element(By.LINK_TEXT, ">"))
            next_page_button.click()

    #INFO: PAGE ACTION ENDS
    driver.quit()
    return cstat


def raw_extract_to_dataframe(entries: List[List[str]]) -> pd.DataFrame:
    column_names = {
        "name": "Player", 
        "total_time": "Total Time", 
        "human_time": "Human Time", 
        "zombie_time": "Zombie Time", 
        "zombie_kills": "Zombies Killed",
        "zombie_hs": "Zombies Killed (HS)",
        "infected": "Infected",
        "items_picked": "Items picked up",
        "boss_killed": "Boss Killed",
        "leader_count": "Leader Count",
        "td_count": "TopDefender Count"
    }
    cstat_objs = []
    for ent in entries:
        obj = PlayerCstat(ent)
        cstat_objs.append(obj)

    df = pd.DataFrame(cstat_objs)
    df.rename(columns=column_names, inplace=True)
    return df


if __name__ == "__main__":
    main()
