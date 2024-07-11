from pydantic import BaseModel


# PriceIncrement
class AOPriceIncrement(BaseModel):
    lowEdge: float = 0.0
    increment: float = 0.0


# json to PriceIncrement
def price_increment_from_json(price_increment_json: str) -> AOPriceIncrement:
    return AOPriceIncrement.model_validate_json(price_increment_json)


# PriceIncrement to json
def price_increment_to_json(price_increment: AOPriceIncrement):

    return price_increment.model_dump_json(
        exclude_none=True, exclude_defaults=True, exclude_unset=True
    )
