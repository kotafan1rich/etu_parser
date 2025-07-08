import asyncio
import logging
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import requests

from src.checker.router import active_users
from src.create_bot import bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


headers = {
    "Accept": "text/html",
    "Accept-Language": "ru,en;q=0.9",
    "Connection": "keep-alive",
    "If-None-Match": '"63a9d2087705d1c89dae206245b142c9"',
    "Origin": "https://abit.etu.ru",
    "Referer": "https://abit.etu.ru/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/134.0.0.0 YaBrowser/25.4.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "YaBrowser";v="25.4", \
            "Yowser";v="2.5"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def program_for_user(url_id: str, users: dict) -> list:
    url = "https://lists.priem.etu.ru/public/list"

    params = {
        "id": url_id,
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None
    html = response.text
    soup = BeautifulSoup(html, "lxml")
    all_mest = int(soup.find("div", class_="places-list").text.strip().split()[-1])
    for row in soup.find_all("tr")[1:]:
        rows_data = [i.text.strip() for i in row.find_all("td")]
        pos = int(rows_data[0])
        id = rows_data[1]
        priority = int(rows_data[2])
        user_data = users.get(id)
        if pos <= all_mest and user_data and priority < user_data["priority"]:
            users.pop(id)
    return users


def get_programs_hrefs() -> list | None:
    url = "https://lists.priem.etu.ru/public/page"
    params = {
        "id": "01978f0d-1f93-7ee6-8067-bee68ca59d4f",
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    html = response.text
    soup = BeautifulSoup(html, "lxml")
    a = soup.find_all("a")
    hrefs = [i.get("href") for i in a]
    ids = []
    for i in hrefs:
        fragment = urlparse(i).fragment
        params = parse_qs(fragment.lstrip("/?"))
        ids.append(params.get("id")[0])
    return ids


def get_main_table():
    url = "https://lists.priem.etu.ru/public/list"

    params = {
        "id": "01978f26-62c1-7a35-8181-19d0798f1454",
        "bodyOnly": "true",
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    html = response.text
    soup = BeautifulSoup(html, "lxml")
    res = {}
    my_pos = -1
    for row in soup.find_all("tr"):
        rows_data = [i.text.strip() for i in row.find_all("td")]
        id = rows_data[1]
        if id == "3675991":
            my_pos = int(rows_data[0])
            continue

        rate = int(rows_data[4])
        priority = int(rows_data[2])
        if rate < 285 and rows_data[3] == "Основные места":
            break

        res[id] = {"rate": rate, "priority": priority}
    return res, my_pos


def get_current_pos() -> tuple[int, int]:
    users_upper, my_pos = get_main_table()
    progams_ids = get_programs_hrefs()
    for programm_id in progams_ids:
        if programm_id != "01978f0d-1f93-7ee6-8067-bee68ca59d4f":
            users_upper = program_for_user(programm_id, users_upper)
    current_pos = len(users_upper) + 1
    return current_pos, my_pos


async def sender():
    while True:
        pos, current_pos = get_current_pos()
        mes = f"Ваша позиция: {pos}({current_pos}) / 68"
        for user_id in active_users:
            await bot.send_message(
                user_id, mes
            )
            logger.info(mes)

        await asyncio.sleep(60 * 60 * 1.5)
