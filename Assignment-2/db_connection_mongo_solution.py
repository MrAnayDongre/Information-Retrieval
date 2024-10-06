from pymongo import MongoClient
import datetime
from collections import defaultdict

def connectDataBase():
    DB_NAME = "CPP"
    DB_HOST = "localhost"
    DB_PORT = 27017

    try:
        client = MongoClient(host=DB_HOST, port=DB_PORT)
        db = client[DB_NAME]
        return db
    except:
        print("Database not connected successfully")

def createDocument(col, docId, docText, docTitle, docDate, docCat):
    # Tokenize the text and create the terms list
    terms = []
    word_counts = defaultdict(int)
    for word in docText.split():
        word = word.lower().strip('.,!?')
        if word:
            word_counts[word] += 1
    
    for word, count in word_counts.items():
        terms.append({
            "term": word,
            "count": count,
            "num_chars": len(word)
        })

    # Create the document
    document = {
        "_id": docId,
        "title": docTitle,
        "text": docText,
        "num_chars": sum(len(word) for word in docText.split()),
        "date": datetime.datetime.strptime(docDate, "%Y-%m-%d"),
        "category": docCat,
        "terms": terms
    }

    # Insert the document
    col.insert_one(document)

def updateDocument(col, docId, docText, docTitle, docDate, docCat):
    # Tokenize the text and create the terms list (same as in createDocument)
    terms = []
    word_counts = defaultdict(int)
    for word in docText.split():
        word = word.lower().strip('.,!?')
        if word:
            word_counts[word] += 1
    
    for word, count in word_counts.items():
        terms.append({
            "term": word,
            "count": count,
            "num_chars": len(word)
        })

    # Update the document
    col.update_one(
        {"_id": docId},
        {
            "$set": {
                "title": docTitle,
                "text": docText,
                "num_chars": sum(len(word) for word in docText.split()),
                "date": datetime.datetime.strptime(docDate, "%Y-%m-%d"),
                "category": docCat,
                "terms": terms
            }
        }
    )

def deleteDocument(col, docId):
    # Delete the document
    col.delete_one({"_id": docId})

def getIndex(col):
    # Create an inverted index
    inverted_index = defaultdict(lambda: defaultdict(int))
    
    # Iterate through all documents
    for doc in col.find():
        for term in doc['terms']:
            inverted_index[term['term']][doc['title']] = term['count']
    
    # Format the output
    formatted_index = {}
    for term, docs in sorted(inverted_index.items()):
        formatted_index[term] = ', '.join(f"{title}:{count}" for title, count in docs.items())
    
    return formatted_index