from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from transactions.models import Client, Transaction, TransactionStatus
from transactions.schemas import ClientSchema

app = FastAPI(
    title='Transactions app'
)


async def get_client_by_name(name: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Client).filter(Client.name == name)
    res = await session.execute(query)
    return res.scalars().first()


@app.post('/clients')
async def create_new_user(new_client: ClientSchema, session: AsyncSession = Depends(get_async_session)):
    existed_client = await get_client_by_name(new_client.name, session)
    print(existed_client)
    if existed_client:
        raise HTTPException(status_code=400, detail="Клиент с таким именем уже существует")
    stmt = insert(Client).values(**new_client.dict())
    await session.execute(stmt)
    await session.commit()
    return {'status': 200,
            'data': new_client}


@app.get('/clients')
async def get_all_clients(limit: int = 10, offset: int = 0, session: AsyncSession = Depends(get_async_session)):
    query = select(Client).limit(limit).offset(offset)
    res = await session.execute(query)
    return res.all()


async def get_client_by_id(client_id: int, session: AsyncSession = Depends(get_async_session)):
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@app.get('/clients/{cliend_id}')
async def get_client(client_id: int, session: AsyncSession = Depends(get_async_session)):
    return await get_client_by_id(client_id, session)


@app.post('/transactions')
async def add_transaction(client_id: int, amount: float, session: AsyncSession = Depends(get_async_session)):
    transaction = Transaction(client_id=client_id, amount=amount, status=TransactionStatus.QUEUED)

    session.add(transaction)

    await session.commit()

    return {'status': 200,
            'clint_id': client_id,
            'amount': amount,
            'transaction_status': transaction.status,
            'transaction_id': transaction.id}


@app.get('/transactions/{user_id}')
async def get_transactions_from_user(client_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Transaction).where(Transaction.client_id == client_id).order_by(Transaction.created_at)
    res = await session.execute(query)
    res = res.scalars().all()
    return res


@app.get('/transactions/{user_id}/execute')
async def execute_next_transaction(client_id: int, session: AsyncSession = Depends(get_async_session)):
    async with session.begin():
        client = await get_client_by_id(client_id, session)

        query = select(Transaction).where(
            (Transaction.client_id == client_id)
            & (Transaction.status == 'queued')
        ).order_by(Transaction.created_at).with_for_update()
        transaction = await session.execute(query)
        transaction = transaction.scalars().first()

        if not transaction:
            return {'status': 200,
                    'info': 'Нет транзакций в очереди'}

        if client.balance < transaction.amount:
            transaction.status = TransactionStatus.REJECTED
            await session.commit()
            raise HTTPException(status_code=400, detail='Недостаточно средств, транзакция отклонена')
        else:
            client.balance -= transaction.amount
            transaction.status = TransactionStatus.COMPLETED
            await session.commit()
            return {'status_code': 200, 'details': 'Транзакция выполнена'}
