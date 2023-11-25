import os
from dotenv import load_dotenv
import uvicorn

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response

from bson import ObjectId
import motor.motor_asyncio
from pymongo import ReturnDocument

from models import ShareholderModel, UpdateShareholderModel

app = FastAPI()
load_dotenv()

# Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGODB_URL"))
db = client.get_database("company-x")
collection = db.get_collection("shareholders")


@app.get("/")
def read_root():
    """
    A simple health check endpoint to confirm that the API is running.
    """
    return {"Hello": "World"}


@app.get(
    "/shareholders/{id}",
    response_description="Get a shareholder with id",
    response_model=ShareholderModel,
    response_model_by_alias=False,
)
async def get_shareholder(id: str):
    """
    Retrieve a single shareholder record from the database.
    """
    shareholder = await collection.find_one({"_id": ObjectId(id)})

    if shareholder:
        return shareholder

    raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")


@app.get(
    "/shareholders/",
    response_description="Get all shareholders",
    response_model=list[ShareholderModel],
    response_model_by_alias=False,
)
async def get_all_shareholders():
    """
    Retrieve all shareholder records from the database.
    """
    shareholders = await collection.find().to_list(length=None)
    return shareholders


@app.post(
    "/shareholders/",
    response_description="Add new shareholder",
    response_model=ShareholderModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_shareholder(shareholder: ShareholderModel = Body(...)):
    """
    Insert a new shareholder record.

    A unique `id` will be created and provided in the response.
    """
    new_shareholder = await collection.insert_one(
        shareholder.model_dump(by_alias=True, exclude=["id"])
    )
    created_shareholder = await collection.find_one(
        {"_id": new_shareholder.inserted_id}
    )
    return created_shareholder


@app.delete("/shareholders/{id}", response_description="Delete a shareholder")
async def delete_shareholder(id: str):
    """
    Remove a single shareholder record from the database.
    """
    delete_result = await collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")


@app.put(
    "/shareholders/{id}",
    response_description="Update a shareholder",
    response_model=ShareholderModel,
    response_model_by_alias=False,
)
async def update_shareholder(id: str, shareholder: UpdateShareholderModel = Body(...)):
    """
    Update individual fields of an existing shareholder record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    shareholder = {
        k: v for k, v in shareholder.model_dump(by_alias=True).items() if v is not None
    }

    if len(shareholder) >= 1:
        update_result = await collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": shareholder},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")

    # The update is empty, but we should still return the matching document:
    if (existing_shareholder := await collection.find_one({"_id": id})) is not None:
        return existing_shareholder

    raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")


@app.put(
    "/shareholders/{id}/transactions",
    response_description="Append a new transaction",
    response_model=ShareholderModel,
    response_model_by_alias=False,
)
async def append_transaction(id: str, transaction: int):
    """
    Append a new transaction to the transactions list of a shareholder.
    Update the "shares" field accordingly.
    """
    shareholder = await collection.find_one({"_id": ObjectId(id)})
    if shareholder is None:
        raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")

    updated_transactions = shareholder.get("transactions", []) + [transaction]
    updated_shares = shareholder.get("shares", 0) + transaction

    update_result = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": {"transactions": updated_transactions, "shares": updated_shares}},
        return_document=ReturnDocument.AFTER,
    )

    if update_result is not None:
        return update_result

    raise HTTPException(status_code=404, detail=f"Shareholder {id} not found")


if __name__ == "__main__":
    uvicorn.run(
        'main:app',
        reload=True
    )