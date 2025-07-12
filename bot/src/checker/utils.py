import asyncio
import logging
from urllib.parse import urlparse, parse_qs
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from src.checker.router import active_users
from src.create_bot import bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HEADERS = {
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


class EtuParser:
    PROGRAMS = {
        "Прикладная математика и информатика": {
            "code": "01.03.02",
            "id": "01978f26-62c1-7a35-8181-19d07b9aa40e",
            "general_budget_seats": 70,
        },
        "Информатика и вычислительная техника (Искусственный интеллект)": {
            "code": "09.03.01",
            "id": "01978f26-62c1-7a35-8181-19d07b0d3074",
            "general_budget_seats": 65,
        },
        "Информатика и вычислительная техника (Компьютерное моделирование и проектирование)": {
            "code": "09.03.01",
            "id": "01978f26-62c2-74d0-bc95-6f2f7efef844",
            "general_budget_seats": 45,
        },
        "Информационные системы и технологии": {
            "code": "09.03.02",
            "id": "01978f26-62c1-7a35-8181-19d07a35c71a",
            "general_budget_seats": 66,
        },
        "Программная инженерия": {
            "code": "09.03.04",
            "id": "01978f26-62c1-7a35-8181-19d0798f1454",
            "general_budget_seats": 44,
        },
        "Компьютерная безопасность": {
            "code": "10.05.01",
            "id": "01978f26-62c1-7a35-8181-19d074e030c9",
            "general_budget_seats": 29,
        },
        "Радиотехника (Системы компьютерного зрения)": {
            "code": "11.03.01",
            "id": "01978f26-62c1-7a35-8181-19d078fa5109",
            "general_budget_seats": 17,
        },
        "Радиотехника (Цифровые системы локации, связи и навигации)": {
            "code": "11.03.01",
            "id": "01978f26-62c2-74d0-bc95-6f2f7db82454",
            "general_budget_seats": 23,
        },
        "Инфокоммуникационные технологии и системы связи": {
            "code": "11.03.02",
            "id": "01978f26-62c2-74d0-bc95-6f2f7e16128a",
            "general_budget_seats": 50,
        },
        "Конструирование и технология электронных средств": {
            "code": "11.03.03",
            "id": "01978f26-62c1-7a35-8181-19d07922eaf2",
            "general_budget_seats": 17,
        },
        "Электроника и наноэлектроника": {
            "code": "11.03.04",
            "id": "01978f26-62c1-7a35-8181-19d078366de1",
            "general_budget_seats": 144,
        },
        "Радиоэлектронные системы и комплексы": {
            "code": "11.05.01",
            "id": "01978f26-62c1-7a35-8181-19d0798f07ab",
            "general_budget_seats": 4,
        },
        "Приборостроение (Интеллектуальные системы)": {
            "code": "12.03.01",
            "id": "01978f26-62c2-74d0-bc95-6f2f7dc34dcd",
            "general_budget_seats": 75,
        },
        "Биотехнические системы и технологии": {
            "code": "12.03.04",
            "id": "01978f26-62c1-7a35-8181-19d0726ef831",
            "general_budget_seats": 41,
        },
        "Электроэнергетика и электротехника": {
            "code": "13.03.02",
            "id": "01978f26-62c1-7a35-8181-19d073fe3fdb",
            "general_budget_seats": 62,
        },
        "Мехатроника и робототехника": {
            "code": "15.03.06",
            "id": "01978f26-62c1-7a35-8181-19d07366ee1c",
            "general_budget_seats": 1,
        },
        "Техносферная безопасность": {
            "code": "20.03.01",
            "id": "01978f26-62c1-7a35-8181-19d071ac9b3a",
            "general_budget_seats": 24,
        },
        "Управление качеством": {
            "code": "27.03.02",
            "id": "01978f26-62c1-7a35-8181-19d077fe9e14",
            "general_budget_seats": 16,
        },
        "Системный анализ и управление": {
            "code": "27.03.03",
            "id": "01978f26-62c1-7a35-8181-19d074435fb0",
            "general_budget_seats": 15,
        },
        "Управление в технических системах (Автоматика и робототехнические системы)": {
            "code": "27.03.04",
            "id": "01978f26-62c1-7a35-8181-19d073071d98",
            "general_budget_seats": 62,
        },
        "Управление в технических системах (Компьютерные интеллектуальные технологии управления в технических системах)": {
            "code": "27.03.04",
            "id": "01978f26-62c1-7a35-8181-19d07410563f",
            "general_budget_seats": 29,
        },
        "Инноватика": {
            "code": "27.03.05",
            "id": "01978f26-62c1-7a35-8181-19d077328fa5",
            "general_budget_seats": 9,
        },
        "Нанотехнологии и микросистемная техника": {
            "code": "28.03.01",
            "id": "01978f26-62c1-7a35-8181-19d07c7a8562",
            "general_budget_seats": 46,
        },
        "Реклама и связи с общественностью": {
            "code": "42.03.01",
            "id": "01978f26-62c1-7a35-8181-19d0768b385d",
            "general_budget_seats": 0,
        },
        "Лингвистика": {
            "code": "45.03.02",
            "id": "01978f26-62c1-7a35-8181-19d075c339dc",
            "general_budget_seats": 6,
        },
    }

    def __init__(self, session: ClientSession):
        self.session = session

    async def program_for_user(self, url_id: str, users: dict) -> list:
        url = "https://lists.priem.etu.ru/public/list"

        params = {
            "id": url_id,
        }
        async with self.session.get(url=url, params=params, timeout=5) as response:
            if response.status != 200:
                return None
            html = await response.text()
            soup = BeautifulSoup(html, "lxml")
            name = soup.find("div", id="header").find("h2").text
            all_mest = self.PROGRAMS[name]["general_budget_seats"]
            users_in_program = 0
            for row in soup.find_all("tr")[1:]:
                if users_in_program < all_mest:
                    rows_data = [i.text.strip() for i in row.find_all("td")]
                    id = rows_data[1]
                    priority = int(rows_data[2])
                    user_data = users.get(id)
                    if user_data and priority < user_data["priority"]:
                        users.pop(id)
                        users_in_program += 1
                else:
                    break
            return users

    async def get_programs_ids(self) -> list | None:
        url = "https://lists.priem.etu.ru/public/page"
        params = {
            "id": "01978f0d-1f93-7ee6-8067-bee68ca59d4f",
        }
        async with self.session.get(url=url, params=params, timeout=5) as response:
            if response.status != 200:
                return None

            html = await response.text()
            soup = BeautifulSoup(html, "lxml")
            tr = soup.find("table", class_="table table-bordered").find_all("tr")
            for i in tr:
                td = i.find_all("td")
                if td:
                    name = td[1].text
                    budget = td[2].find("a").get("href")
                    fragment = urlparse(budget).fragment
                    params = parse_qs(fragment.lstrip("/?"))
                    id = params.get("id")[0]
                    self.PROGRAMS[name]["id"] = id

    async def get_main_table(self):
        url = "https://lists.priem.etu.ru/public/list"

        params = {
            "id": "01978f26-62c1-7a35-8181-19d0798f1454",
            "bodyOnly": "true",
        }

        async with self.session.get(url=url, params=params, timeout=5) as response:
            if response.status != 200:
                return None

            html = await response.text()
            soup = BeautifulSoup(html, "lxml")
            res = {}
            my_pos = 0
            for row in soup.find_all("tr"):
                rows_data = [i.text.strip() for i in row.find_all("td")]
                if rows_data:
                    id = rows_data[1]
                    quata = rows_data[3]
                    if id == "3675991" or quata not in ("БВИ", "Основные места"):
                        my_pos = int(rows_data[0])
                        continue

                    rate = int(rows_data[4])
                    priority = int(rows_data[2])

                    if rate < 285 and quata == "Основные места":
                        break

                    res[id] = {"rate": rate, "priority": priority}
            return res, my_pos

    async def get_current_pos(self) -> tuple[int | None, int | None]:
        users_upper, my_pos = await self.get_main_table()
        logger.info(f"Users upper: {len(users_upper)}, my_pos: {my_pos}")

        if users_upper and my_pos:
            await self.get_programs_ids()
            logger.info(f"Program ids count: {len(self.PROGRAMS)}")

            for name in self.PROGRAMS:
                program_id = self.PROGRAMS[name]["id"]
                if program_id != "01978f0d-1f93-7ee6-8067-bee68ca59d4f":
                    users_upper = await self.program_for_user(program_id, users_upper)
                    logger.info(f"{program_id} parsed")

            current_pos = len(users_upper) + 1
        return current_pos, my_pos


async def sender():
    while True:
        async with ClientSession(headers=HEADERS) as session:
            parser = EtuParser(session=session)
            pos, current_pos = await parser.get_current_pos()
            mes = f"Ваша позиция: {pos}({current_pos}) / 44"

            for user_id in active_users:
                await bot.send_message(user_id, mes)

            logger.info(mes)
            logger.info(f"end pars\n{'-' * 100}")

        await asyncio.sleep(60 * 60 * 1.5)
