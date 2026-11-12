from pydantic import BaseModel


class CountryOut(BaseModel):
    id: str
    name: str
    cuisine: str
    iso2: str
    iso3: str
    dish_count: int
