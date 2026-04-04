from pydantic import BaseModel


class Ticket(BaseModel):
    user_id: int
    username: str
    phone: str
    image_url: str
    debt: float

    class Config:
        from_attributes = True