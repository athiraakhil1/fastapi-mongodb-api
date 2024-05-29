from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from typing import List

app = FastAPI()

# Initialize MongoDB client and collection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.books_database
collection = db.books_collection

class Book(BaseModel):
    title: str
    author: str
    summary: str

class BookInDB(Book):
    id: str

# Utility function to convert MongoDB document to Pydantic model
def book_helper(book) -> BookInDB:
    return BookInDB(id=str(book["_id"]), title=book["title"], author=book["author"], summary=book["summary"])

@app.post("/books/", response_model=BookInDB)
async def create_book(book: Book):
    book_dict = book.dict()
    result = await collection.insert_one(book_dict)
    new_book = await collection.find_one({"_id": result.inserted_id})
    return book_helper(new_book)

@app.get("/books/", response_model=List[BookInDB])
async def get_books():
    books = []
    async for book in collection.find():
        books.append(book_helper(book))
    return books

@app.get("/books/{book_id}", response_model=BookInDB)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_helper(book)

@app.put("/books/{book_id}", response_model=BookInDB)
async def update_book(book_id: str, book: Book):
    update_result = await collection.update_one(
        {"_id": ObjectId(book_id)}, {"$set": book.dict()}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_book = await collection.find_one({"_id": ObjectId(book_id)})
    return book_helper(updated_book)

@app.delete("/books/{book_id}", response_model=BookInDB)
async def delete_book(book_id: str):
    delete_result = await collection.delete_one({"_id": ObjectId(book_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}