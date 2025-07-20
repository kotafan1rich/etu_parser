import asyncio
import json
import logging
import random
from urllib.parse import parse_qs, urlparse

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from src.checker.router import active_users
from src.create_bot import bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from aiogram.exceptions import TelegramBadRequest

ua = UserAgent()


class EtuParser:
    HEADERS = {
        "Accept": "text/html",
        "Accept-Language": "ru,en;q=0.9",
        "Connection": "keep-alive",
    }

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

    def __init__(self, upgu_user_id: str, session: ClientSession):
        self.user_id_in_etu: str = upgu_user_id
        self.session: ClientSession = session

    async def program_for_user(self, url_id: str, users: dict) -> list:
        url = "https://lists.priem.etu.ru/public/list"

        params = {
            "id": url_id,
        }
        async with self.session.get(
            url=url, params=params, headers=EtuParser.HEADERS
        ) as response:
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
                    user_data = users.get(id, 0)
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
        async with self.session.get(
            url=url, params=params, headers=EtuParser.HEADERS
        ) as response:
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
                    id = params.get("id", (0,))[0]
                    self.PROGRAMS[name]["id"] = id

    async def get_main_table(self):
        url = "https://lists.priem.etu.ru/public/list"

        params = {
            "id": "01978f26-62c1-7a35-8181-19d0798f1454",
            "bodyOnly": "true",
        }

        async with self.session.get(
            url=url, params=params, headers=EtuParser.HEADERS
        ) as response:
            if response.status != 200:
                return None

            html = await response.text()
            soup = BeautifulSoup(html, "lxml")
            data = []
            for row in soup.find_all("tr"):
                rows_data = [i.text.strip() for i in row.find_all("td")]
                if rows_data:
                    id = rows_data[1]
                    priority = int(rows_data[2]) if rows_data[2] else 0
                    quata = rows_data[3]
                    rate = int(rows_data[4]) if rows_data[4] else 0
                    rate_without = int(rows_data[5]) if rows_data[5] else 0
                    data.append(
                        (
                            id,
                            priority,
                            int(quata in ("БВИ", "Основные места")),
                            rate,
                            rate_without,
                        )
                    )

            data.sort(key=lambda x: (x[3], x[4], x[2]), reverse=True)
            res = {}
            for rows_data in data:
                id = rows_data[0]
                priority = int(rows_data[1])
                quata = rows_data[2]
                rate = int(rows_data[3])
                if str(id) == str(self.user_id_in_etu):
                    break
                res[id] = {"rate": rate, "priority": priority}
            return res

    async def get_current_pos(self, programm_name) -> tuple[int | None, int | None]:
        users_upper = await self.get_main_table()
        my_pos = len(users_upper) + 1
        logger.info(f"Users upper: {len(users_upper)}, my_pos: {my_pos}")

        if users_upper and my_pos:
            await self.get_programs_ids()
            logger.info(f"Program ids count: {len(self.PROGRAMS)}")

            for name in self.PROGRAMS:
                program_id = self.PROGRAMS[name]["id"]
                if name != programm_name:
                    users_upper = await self.program_for_user(program_id, users_upper)
                logger.info(f"Program Etu {name} - parsed")
            current_pos = len(users_upper) + 1
        return current_pos, my_pos


class PolyParser:
    HEADERS = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://my.spbstu.ru",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="136", "YaBrowser";v="25.6", "Not.A/Brand";v="99", "Yowser";v="2.5"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua.random,
        "x-csrftoken": str(random.randint(10000, 99999)),
    }

    PROGRAMS_IDS = [
        776,  # 01.03.02 Прикладная математика и информатика
        423,  # 02.03.01 Математика и компьютерные науки
        450,  # 02.03.03 матобес и администрирование информационных систем
        287,  # 09.03.01 Информатика и вычислительная техника
        340,  # 09.03.02 Информационные системы и технологии
        765,  # 09.03.03 Прикладная информатика
        847,  # 09.03.04 Программная инженерия
        298,  # 10.03.01 Информационная безопасность
        360,  # 10.05.01 Компьютерная безопасность
        315,  # 10.05.03 Информационная безопасность автоматизированных систем
        320,  # 10.05.04 Информационно-аналитические системы безопасности
        35,  # 38.03.05 Бизнес-информатика
        243,  # 45.03.04 Интеллектуальные системы в гуманитарной сфере
    ]

    def __init__(self, session: ClientSession, epgu_user_id: str):
        self.session: ClientSession = session
        self.upgu_user_id: str = epgu_user_id

    async def update_cookie(self) -> None:
        async with self.session.get(
            "https://my.spbstu.ru/home/abit/list-applicants/bachelor",
            headers=self.HEADERS,
        ) as response:
            if response.status != 200:
                response.raise_for_status()
            cookies = response.cookies
            cookies_dict = dict(cookies.items())
            self.session.cookie_jar.update_cookies(cookies_dict)

    async def get_program_ids(self) -> list[str]:
        json_data = {
            "id_1": "2",
            "id_2": "1",
            "education_level": "bachelor",
        }
        async with self.session.post(
            "https://my.spbstu.ru/home/get-code-list",
            headers=self.HEADERS,
            json=json_data,
        ) as response:
            if response.status != 200:
                response.raise_for_status()
            json_data = await response.json()
            codes = json_data.get("code_list", [])
            valid_ids = [
                code.get("id")
                for code in codes
                if "ИНО" not in code.get("title", False)
            ]
            return valid_ids

    async def get_program_table(self, program_id: str) -> dict:
        params = {
            "filter_1": "2",
            "filter_2": "1",
            "filter_3": program_id,
            "education_level": "bachelor",
        }
        async with self.session.get(
            "https://my.spbstu.ru/home/get-abit-list",
            params=params,
            headers=self.HEADERS,
        ) as response:
            if response.status != 200:
                response.raise_for_status()
            json_data = await response.json()
            results = json_data.get("results", {})
            table = {}
            k = 1
            for i in results:
                if i["code"] not in table:
                    table[i["code"]] = i
                    i["num"] = k
                    k += 1
            return table

    async def get_places(self, program_id: str) -> int:
        json_data = {
            "id_3": program_id,
            "education_level": "bachelor",
        }
        async with self.session.post(
            "https://my.spbstu.ru/home/get-direction-info",
            headers=self.HEADERS,
            json=json_data,
        ) as response:
            if response.status != 200:
                response.raise_for_status()
            json_data = await response.json()
            return int(json_data[0].get("places", 0))

    def get_concurents(self, table: dict, my_pos: int) -> dict:
        concurrents = {}
        for key, value in table.items():
            if value["num"] < my_pos:
                concurrents[key] = value
        return concurrents

    def clear_concurrents(self, concurrents: dict, table: dict, places: int) -> dict:
        for code in concurrents.copy().keys():
            if code in table:
                cur_pr = concurrents[code]["priority"]
                prog_pr = table[code]["priority"]
                prog_pos = table[code]["num"]
                if prog_pos <= places and cur_pr > prog_pr:
                    concurrents.pop(code)
        return concurrents


class BonchParser:
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://priem.sut.ru",
        "Referer": "https://priem.sut.ru/spisok-abiturientov",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ua.random,
        "sec-ch-ua": '"Chromium";v="136", "YaBrowser";v="25.6", "Not.A/Brand";v="99", "Yowser";v="2.5"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        # 'Cookie': '_ym_uid=1745337331878608362; _ym_d=1745337331; PHPSESSID=opjvt7tupba02h2a41st21d6s6; _ym_isad=2; _ym_visorc=w',
    }

    def __init__(self, session: ClientSession, epgu_user_id: str):
        self.session: ClientSession = session
        self.epgu_user_id: str = epgu_user_id

    async def update_cookie(self) -> None:
        async with self.session.get(
            "https://priem.sut.ru/spisok-abiturientov",
            headers=self.HEADERS,
        ) as response:
            if response.status != 200:
                response.raise_for_status()
            cookies = response.cookies
            cookies_dict = dict(cookies.items())
            self.session.cookie_jar.update_cookies(cookies_dict)

    async def get_programs_ids(self) -> list[int]:
        data = 'jsonData={"action":"get_spec","education_base_to":"11","training_form":"4","general":"101","training_type":"1"}'
        url = "https://priem.sut.ru/new_site/inc/ajax_abitur_2025.php"
        async with self.session.post(url, headers=self.HEADERS, data=data) as response:
            if response.status != 200:
                response.raise_for_status()
            text_response = await response.text()
            json_data = json.loads(text_response)
            html = json_data.get("selecter")
            soup = BeautifulSoup(html, "lxml")
            ids = []
            for i in soup.find_all("option"):
                ids.append(int(i.get("value")))
            return ids

    async def get_soup(self, data, url, is_post: bool = False):
        if is_post:
            response = await self.session.post(url, headers=self.HEADERS, data=data)
        else:
            response = await self.session.get(url, headers=self.HEADERS, data=data)
        if response.status != 200:
            response.raise_for_status()
        html = await response.text()
        soup = BeautifulSoup(html, "lxml")
        response.close()
        return soup

    async def get_program_table(self, soup, program_id: int):
        table = soup.find("table", id=f"t_{program_id}")
        res = {}
        for tr in table.find_all("tr", style="cursor: pointer;   "):
            rows_data = [i.text for i in tr.find_all("td")]
            num = int(rows_data[0].strip("."))
            id = rows_data[1]
            priority = int(rows_data[3])
            rate = int(rows_data[7])
            res[id] = {"num": num, "priority": priority, "rate": rate}
        return res

    async def get_places(self, soup):
        places = int(
            soup.find("td", style="background: #efefef;padding: 5px 2px;").text
        )
        return places

    def get_concurents(self, table: dict, my_pos: int) -> dict:
        concurrents = {}
        for key, value in table.items():
            if value["num"] < my_pos:
                concurrents[key] = value
        return concurrents

    async def clear_concurrents(self, table: dict, concurrents: dict, places: int):
        for id in concurrents.copy().keys():
            if id in table:
                cur_pr = concurrents[id]["priority"]
                prog_pr = table[id]["priority"]
                prog_pos = table[id]["num"]
                if prog_pos <= places and cur_pr > prog_pr:
                    concurrents.pop(id)
        return concurrents


async def get_my_bonch_pose(epgu_user_id: str) -> tuple[int, int, int]:
    async with ClientSession(timeout=ClientTimeout(total=60 * 5)) as session:
        bonch_parser = BonchParser(
            session=session,
            epgu_user_id=epgu_user_id,
        )
        await bonch_parser.update_cookie()
        program_ids = await bonch_parser.get_programs_ids()
        target_id = 399153
        data = {
            "general": "101",
            "education_base_to": "11",
            "training_form": "4",
            "training_type": "1",
            "1cunv_groupab": target_id,
            "action": "get_result_new",
            "rekzach": "0",
        }
        url = "https://priem.sut.ru/spisok-abiturientov"
        soup = await bonch_parser.get_soup(data=data, url=url, is_post=True)
        target_program_table = await bonch_parser.get_program_table(
            soup=soup, program_id=target_id
        )
        target_program_places = await bonch_parser.get_places(soup=soup)
        my_pos: int = target_program_table[epgu_user_id]["num"]
        concurrents = bonch_parser.get_concurents(
            table=target_program_table, my_pos=my_pos
        )
        logger.info(
            f"Concurents count: {len(concurrents)}, my_pos: {my_pos}, places: {target_program_places}"
        )
        for program_id in program_ids:
            if program_id == target_id:
                continue
            data["1cunv_groupab"] = program_id
            soup = await bonch_parser.get_soup(data=data, url=url, is_post=True)
            places = await bonch_parser.get_places(soup=soup)
            table_data = await bonch_parser.get_program_table(
                soup=soup, program_id=program_id
            )
            concurrents = await bonch_parser.clear_concurrents(
                table=table_data, concurrents=concurrents, places=places
            )
            logger.info(f"Bonch Program {program_id} - parsed")

        return my_pos, len(concurrents), target_program_places


async def get_my_poly_pos(epgu_user_id: str) -> tuple[int, int, int]:
    async with ClientSession(timeout=ClientTimeout(60 * 5)) as session:
        select_program_id = "847"  # Программная инженерия
        logger.info("Start Poly Parser")
        parser = PolyParser(session, epgu_user_id)
        await parser.update_cookie()
        try:
            target_program_table = await parser.get_program_table(select_program_id)
            target_program_places = await parser.get_places(select_program_id)
            my_pos = target_program_table.get(epgu_user_id, {}).get("num", 0)
        except TimeoutError:
            await asyncio.sleep(60)
            logger.info("Sleep 60 sec...")

            target_program_table = await parser.get_program_table(select_program_id)
            target_program_places = await parser.get_places(select_program_id)
            my_pos = target_program_table.get(epgu_user_id, {}).get("num", 0)

        if not my_pos or not target_program_table:
            return None
        concurents = parser.get_concurents(target_program_table, my_pos)
        logger.info(
            f"Concurents count: {len(concurents)}, my_pos: {my_pos}, places: {target_program_places}"
        )
        for program_id in PolyParser.PROGRAMS_IDS:
            if program_id == select_program_id:
                continue
            try:
                program_table = await parser.get_program_table(program_id)
            except TimeoutError:
                await asyncio.sleep(60)
                logger.info("Sleep 60 sec...")

                program_table = await parser.get_program_table(program_id)
            places = await parser.get_places(program_id)
            concurents = parser.clear_concurrents(
                concurrents=concurents, table=program_table, places=places
            )
            logger.info(f"Poly Program {program_id} - parsed")
    return my_pos, len(concurents), target_program_places


async def get_my_etu_pos(
    user_id_in_etu: str, programm_name: str = "Программная инженерия"
) -> tuple[int | None, int | None, int]:
    async with ClientSession(timeout=ClientTimeout(60 * 5)) as session:
        logger.info("Start Etu Parser")
        parser = EtuParser(upgu_user_id=user_id_in_etu, session=session)
        pos, current_pos = await parser.get_current_pos(programm_name=programm_name)
        general_budget_seats = EtuParser.PROGRAMS[programm_name]["general_budget_seats"]
    return pos, current_pos, general_budget_seats


async def sender(
    programm_name: str = "Программная инженерия", epgu_user_id: str = "3675991"
):
    while True:
        etu_data = await get_my_etu_pos(
            user_id_in_etu=epgu_user_id,
            programm_name=programm_name,
        )
        poly_data = await get_my_poly_pos(epgu_user_id=epgu_user_id)
        # bonch_data = await get_my_bonch_pose(epgu_user_id=epgu_user_id)

        results = []
        if etu_data:
            etu_pos, etu_concurents, etu_places = etu_data
            res_etu = f"ЛЭТИ: {etu_concurents + 1} ({etu_pos}) / {etu_places} мест"
            results.append(res_etu)
        if poly_data:
            poly_pos, poly_concurents, poly_places = poly_data
            res_poly = (
                f"Политех: {poly_pos} ({poly_concurents + 1}) / {poly_places} мест"
            )
            results.append(res_poly)
        # if bonch_data:
        #     bonch_pos, bonch_concurents, bonch_places = bonch_data
        #     res_bonch = (
        #         f"Бонч: {bonch_pos} ({bonch_concurents + 1}) / {bonch_places} мест"
        #     )
        #     results.append(res_bonch)

        if results:
            mes = "\n".join(results)
            for user_id in active_users:
                try:
                    await bot.send_message(user_id, mes)
                except TelegramBadRequest:
                    ...

            logger.info(mes)
            logger.info(f"end pars\n{'-' * 100}")
        else:
            logger.error("Parsing error, no data received")
        delay = 60 * 60 * 1.5
        await asyncio.sleep(delay)
