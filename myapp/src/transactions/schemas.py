from pydantic.main import BaseModel


class ClientSchema(BaseModel):
    name: str
    balance: float


class TransactionCreate(BaseModel):
    client_id: int
    amount: float
