from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.models import mongodb
from app.models.shop import ShopModel
from app.shop_scraper import NaverShopScraper
import re

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    fav_count = await mongodb.engine.count(ShopModel, ShopModel.is_favorite == True)
    return templates.TemplateResponse(request, "index.html", {"title": "쇼핑 검색", "fav_count": fav_count})

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    fav_count = await mongodb.engine.count(ShopModel, ShopModel.is_favorite == True)
    if not q:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"message": "검색어를 입력해주세요", "fav_count": fav_count},
        )

    scraper = NaverShopScraper()
    items = await scraper.search(q, 3)

    favorite_shops = await mongodb.engine.find(ShopModel, ShopModel.is_favorite == True)
    favorite_images = [shop.image for shop in favorite_shops]

    shop_models = []
    for item in items:
        lprice = int(item.get("lprice") or 0)
        shop_model = ShopModel(
            keyword=q,
            title=strip_html(item.get("title", "")),
            link=item.get("link", ""),
            image=item.get("image", ""),
            lprice=lprice,
            mall_name=item.get("mallName", ""),
            brand=item.get("brand", "") or "",
        )
        if shop_model.image in favorite_images:
            shop_model.is_favorite = True
        shop_models.append(shop_model)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "keyword": q,
            "items": shop_models,
            "next_url": f"/search?q={q}",
            "fav_count": fav_count,
        },
    )

@app.post("/favorites")
async def toggle_favorite(
    request: Request,
    keyword: str = Form(...),
    title: str = Form(...),
    link: str = Form(...),
    image: str = Form(...),
    lprice: int = Form(...),
    mall_name: str = Form(...),
    brand: str = Form(""),
    next_url: str = Form("/"),
):
    favorite_shop = await mongodb.engine.find_one(
        ShopModel,
        (ShopModel.image == image) & (ShopModel.is_favorite == True)
    )
    if favorite_shop:
        await mongodb.engine.delete(favorite_shop)
    else:
        shop = ShopModel(
            keyword=keyword,
            title=title,
            link=link,
            image=image,
            lprice=lprice,
            mall_name=mall_name,
            brand=brand or "",
            is_favorite=True,
        )
        await mongodb.engine.save(shop)
    return RedirectResponse(url=next_url, status_code=303)

@app.get("/favorites", response_class=HTMLResponse)
async def favorites(request: Request):
    items = await mongodb.engine.find(ShopModel, ShopModel.is_favorite == True)
    fav_count = len(items)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "즐겨찾기 목록",
            "items": items,
            "next_url": "/favorites",
            "fav_count": fav_count,
        },
    )

@app.on_event("startup")
async def on_app_start():
    print("서버 시작")
    mongodb.connect()

@app.on_event("shutdown")
async def on_app_shutdown():
    print("서버 종료")
    mongodb.close()
