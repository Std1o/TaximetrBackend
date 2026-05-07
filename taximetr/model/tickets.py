from pydantic import BaseModel


class Ticket(BaseModel):
    user_id: int
    username: str
    phone: str
    image_url: str
    debt: float
    hours: int
    settings_id: int

    class Config:
        from_attributes = True