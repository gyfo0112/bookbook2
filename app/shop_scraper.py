import asyncio
import aiohttp
from app.config import NAVER_API_ID, NAVER_API_SECRET

class NaverShopScraper:
    NAVER_API_SHOP = "https://openapi.naver.com/v1/search/shop"

    @staticmethod
    async def fetch(session, url, headers):
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result["items"]
        return []

    def unit_url(self, keyword, start, sort="sim", filter=""):
        url = f"{self.NAVER_API_SHOP}?query={keyword}&display=10&start={start}&sort={sort}"
        if filter:
            url += f"&filter={filter}"
        return {
            "url": url,
            "headers": {
                "X-Naver-Client-Id": NAVER_API_ID,
                "X-Naver-Client-Secret": NAVER_API_SECRET,
            },
        }

    async def search(self, keyword, total_page, sort="sim", filter=""):
        apis = [self.unit_url(keyword, 1 + i * 10, sort, filter) for i in range(total_page)]
        async with aiohttp.ClientSession() as session:
            all_data = await asyncio.gather(
                *[
                    NaverShopScraper.fetch(session, api["url"], api["headers"])
                    for api in apis
                ]
            )
            result = []
            for data in all_data:
                for item in data:
                    result.append(item)
            return result
