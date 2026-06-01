from odmantic import Model
from typing import Optional

class ShopModel(Model):
    keyword: str
    title: str
    link: str
    image: str
    lprice: int
    mall_name: str
    brand: str = ""
    is_favorite: bool = False

    model_config = {"collection": "shops"}
