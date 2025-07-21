import asyncio
import json
import logging
import random

from aiogram.exceptions import TelegramBadRequest
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from src.checker.models import Abitur, QuotaType
from src.checker.router import active_users
from src.create_bot import bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ua = UserAgent()


class BaseParser:
    def __init__(self, epgu_user_id: str, session: ClientSession):
        self.epgu_uer_id: str = epgu_user_id
        self.session: ClientSession = session

    async def get_soup(self, url: str, is_post: bool = False, **kwargs):
        if is_post:
            response = await self.session.post(url, **kwargs)
        else:
            response = await self.session.get(url, **kwargs)
        if response.status != 200:
            response.raise_for_status()
        html = await response.text()
        soup = BeautifulSoup(html, "lxml")
        response.close()
        return soup

    def get_concurrents(self, table: dict[str, Abitur]) -> dict:
        my_pos = table.get(self.epgu_uer_id).num
        concurrents = {}
        for code, abitur in table.items():
            if abitur.num < my_pos:
                concurrents[code] = abitur
        return concurrents

    def clear_concurrents(
        self, concurrents: dict[str, Abitur], table: dict[str, Abitur], places: int
    ) -> dict[str, Abitur]:
        for code in concurrents.copy().keys():
            if code in table:
                cur_pr = concurrents.get(code).priority
                prog_pr = table.get(code).priority
                prog_pos = table.get(code).num
                if prog_pos <= places and cur_pr > prog_pr:
                    concurrents.pop(code)
        return concurrents


class EtuParser(BaseParser):
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
    }

    PROGRAMS_LIST = [value.get("id") for value in PROGRAMS.values()]

    async def get_places(self, soup: BeautifulSoup) -> int:
        name = soup.find("div", id="header").find("h2").text
        all_mest = int(self.PROGRAMS[name]["general_budget_seats"])
        return all_mest

    async def get_program_table(self, soup: BeautifulSoup) -> dict:
        data = {}
        k = 1
        for row in soup.find_all("tr"):
            rows_data = [i.text.strip() for i in row.find_all("td")]
            if rows_data:
                code = rows_data[1]
                priority = int(rows_data[2]) if rows_data[2] else 0
                quota = rows_data[3]
                if quota == "БВИ":
                    quota = QuotaType.NO_EXAM
                elif quota == "Основные места":
                    quota = QuotaType.GENERAL
                else:
                    quota = QuotaType.OTHER
                rate = int(rows_data[4]) if rows_data[4] else 0
                if quota in (QuotaType.NO_EXAM, QuotaType.GENERAL) and code not in data:
                    data[code] = Abitur(
                        code=code, num=k, rate=rate, priority=priority, quota=quota
                    )
                    k += 1
        return data

    async def get_current_pos(
        self, program_name
    ) -> tuple[int | None, int | None, int | None]:
        target_program_id = self.PROGRAMS[program_name]["id"]
        url = "https://lists.priem.etu.ru/public/list"
        params = {
            "id": target_program_id,
        }
        soup = await self.get_soup(
            url=url, is_post=False, params=params, headers=self.HEADERS
        )
        target_program_table = await self.get_program_table(soup=soup)
        concurrents = self.get_concurrents(target_program_table)
        my_pos = len(concurrents) + 1
        target_program_places = self.PROGRAMS[program_name]["general_budget_seats"]
        logger.info(
            f"concurrents count: {len(concurrents)}, my_pos: {my_pos}, places: {target_program_places}"
        )
        if concurrents and my_pos:
            for name in self.PROGRAMS:
                program_id = self.PROGRAMS[name]["id"]
                if program_id != target_program_id:
                    params["id"] = program_id
                    soup = await self.get_soup(
                        url=url, is_post=False, params=params, headers=self.HEADERS
                    )
                    program_table = await self.get_program_table(soup=soup)
                    places = self.PROGRAMS[name]["general_budget_seats"]
                    concurrents = self.clear_concurrents(
                        concurrents=concurrents, table=program_table, places=places
                    )
                logger.info(f"Program Etu {program_id} - parsed")

        return my_pos, len(concurrents), target_program_places


class PolyParser(BaseParser):
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

    def clear_concurrents(
        self, concurrents: dict[str, Abitur], table: dict[str, Abitur], places: int
    ) -> dict[str, Abitur]:
        for code in concurrents.copy().keys():
            if code in table:
                cur_pr = concurrents.get(code).priority
                prog_pr = table.get(code).priority
                prog_pos = table.get(code).num
                rate = concurrents.get(code).rate
                quota = concurrents.get(code).quota
                if (prog_pos <= places and cur_pr > prog_pr) or (
                    rate != 0 and quota == QuotaType.NO_EXAM
                ):
                    concurrents.pop(code)
        return concurrents

    async def get_program_table(self, program_id: str) -> dict[str, Abitur]:
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
            for row_data in results:
                code = row_data.get("code")
                num = k
                rate = int(row_data.get("sum")) if row_data.get("sum") else 0
                priority = row_data.get("priority")
                quota = row_data.get("base")
                if quota == "Нет":
                    quota = QuotaType.GENERAL
                else:
                    quota = QuotaType.NO_EXAM
                if code not in table:
                    table[code] = Abitur(
                        code=code, num=num, quota=quota, priority=priority, rate=rate
                    )
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


class BonchParser(BaseParser):
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

    async def get_program_table(self, soup, program_id: int) -> dict[str, Abitur]:
        table = soup.find("table", id=f"t_{program_id}")
        res = {}
        for tr in table.find_all("tr", style="cursor: pointer;   "):
            rows_data = [i.text for i in tr.find_all("td")]
            num = int(rows_data[0].strip("."))
            code = rows_data[1]
            priority = int(rows_data[3])
            res[code] = {"num": num, "priority": priority}
        return res

    async def get_places(self, soup):
        places = int(
            soup.find("td", style="background: #efefef;padding: 5px 2px;").text
        )
        return places


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
        soup = await bonch_parser.get_soup(
            url=url, is_post=True, data=data, headers=bonch_parser.HEADERS
        )
        target_program_table = await bonch_parser.get_program_table(
            soup=soup, program_id=target_id
        )
        target_program_places = await bonch_parser.get_places(soup=soup)
        my_pos: int = target_program_table.get(epgu_user_id).num
        concurrents = bonch_parser.get_concurrents(table=target_program_table)
        logger.info(
            f"concurrents count: {len(concurrents)}, my_pos: {my_pos}, places: {target_program_places}"
        )
        for program_id in program_ids:
            if program_id == target_id:
                continue
            data["1cunv_groupab"] = program_id
            soup = await bonch_parser.get_soup(
                url=url, is_post=True, data=data, headers=bonch_parser.HEADERS
            )
            places = await bonch_parser.get_places(soup=soup)
            table_data = await bonch_parser.get_program_table(
                soup=soup, program_id=program_id
            )
            concurrents = bonch_parser.clear_concurrents(
                table=table_data, concurrents=concurrents, places=places
            )
            logger.info(f"Bonch Program {program_id} - parsed")

        return my_pos, len(concurrents), target_program_places


async def get_my_poly_pos(epgu_user_id: str) -> tuple[int, int, int]:
    async with ClientSession(timeout=ClientTimeout(60 * 5)) as session:
        select_program_id = "847"  # Программная инженерия
        logger.info("Start Poly Parser")
        parser = PolyParser(session=session, epgu_user_id=epgu_user_id)
        await parser.update_cookie()
        try:
            target_program_table = await parser.get_program_table(select_program_id)
            target_program_places = await parser.get_places(select_program_id)
            my_pos = target_program_table.get(epgu_user_id, {}).num
        except TimeoutError:
            await asyncio.sleep(60)
            logger.info("Sleep 60 sec...")

            target_program_table = await parser.get_program_table(select_program_id)
            target_program_places = await parser.get_places(select_program_id)
            my_pos = target_program_table.get(epgu_user_id, {}).num

        if not my_pos or not target_program_table:
            return None
        concurrents = parser.get_concurrents(target_program_table)
        logger.info(
            f"concurrents count: {len(concurrents)}, my_pos: {my_pos}, places: {target_program_places}"
        )
        for program_id in PolyParser.PROGRAMS_IDS:
            if program_id == select_program_id:
                continue
            try:
                program_table = await parser.get_program_table(program_id)
            except TimeoutError:
                logger.info("Sleep 60 sec...")
                await asyncio.sleep(60)

                program_table = await parser.get_program_table(program_id)
            places = await parser.get_places(program_id)
            concurrents = parser.clear_concurrents(
                concurrents=concurrents, table=program_table, places=places
            )
            logger.info(f"Poly Program {program_id} - parsed")
    return my_pos, len(concurrents), target_program_places


async def get_my_etu_pos(
    epgu_user_id: str, programm_name: str = "Программная инженерия"
) -> tuple[int | None, int | None, int]:
    async with ClientSession(timeout=ClientTimeout(60 * 5)) as session:
        logger.info("Start Etu Parser")
        parser = EtuParser(epgu_user_id=epgu_user_id, session=session)
        pos, current_pos, general_budget_seats = await parser.get_current_pos(
            program_name=programm_name
        )
    return pos, current_pos, general_budget_seats


async def sender(
    programm_name: str = "Программная инженерия", epgu_user_id: str = "3675991"
):
    while True:
        etu_data = await get_my_etu_pos(
            epgu_user_id=epgu_user_id,
            programm_name=programm_name,
        )
        poly_data = await get_my_poly_pos(epgu_user_id=epgu_user_id)
        # bonch_data = await get_my_bonch_pose(epgu_user_id=epgu_user_id)

        results = []
        if etu_data:
            etu_pos, etu_concurrents, etu_places = etu_data
            res_etu = f"ЛЭТИ: {etu_pos} ({etu_concurrents}) / {etu_places} мест"
            results.append(res_etu)
        if poly_data:
            poly_pos, poly_concurrents, poly_places = poly_data
            res_poly = (
                f"Политех: {poly_pos} ({poly_concurrents + 1}) / {poly_places} мест"
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
