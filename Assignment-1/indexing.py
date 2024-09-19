#-------------------------------------------------------------------------
# AUTHOR: ANAY DONGRE
# FILENAME: indexing.py
# SPECIFICATION: This Python program reads documents from a CSV file and computes a document-term matrix using TF-IDF (Term Frequency-Inverse Document Frequency) weights. 
#                It first cleans the documents by removing stopwords (like pronouns and conjunctions) and applying stemming to reduce word variations (e.g., "cats" to "cat"). 
#                The terms "love," "cat," and "dog" are chosen as index terms, and their TF-IDF scores are calculated for each document. 
#                The final output is a matrix where each row represents a document, and each column shows the TF-IDF value for the corresponding term.
# FOR: CS 5180- Assignment #1
# TIME SPENT: 20 min
#-----------------------------------------------------------*/
# Importing some Python libraries
import csv
from collections import defaultdict
import math

# Reading the data in a csv file
documents = []
with open('collection.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    for i, row in enumerate(reader):
        if i > 0:  # skipping the header
            documents.append(row[0])

# Conducting stopword removal for pronouns/conjunctions. Hint: use a set to define stopwords.
stopWords = {'i', 'she', 'he', 'they', 'her', 'his', 'their', 'and', 'the', 'a', 'an'}

# Conducting stemming. Hint: use a dictionary to map word variations to their stem.
stemming = {
    'cats': 'cat',
    'loves': 'love',
    'dogs': 'dog'
}

# Function to clean a document (remove stopwords and apply stemming)
def clean_document(doc):
    words = doc.lower().split()  # Lowercasing and splitting words
    cleaned_words = []
    for word in words:
        if word not in stopWords:  # Remove stopwords
            stemmed_word = stemming.get(word, word)  # Apply stemming
            cleaned_words.append(stemmed_word)
    return cleaned_words

# Cleaned documents
cleaned_documents = [clean_document(doc) for doc in documents]

# Identifying the index terms in the specified order: love, cat, dog
terms = ['love', 'cat', 'dog']

# Function to calculate term frequency (TF)
def calculate_tf(term, document):
    term_count = document.count(term)
    return term_count / len(document) if len(document) > 0 else 0

# Function to calculate inverse document frequency (IDF)
def calculate_idf(term, documents):
    doc_count_with_term = sum(1 for doc in documents if term in doc)
    return math.log10(len(documents) / (doc_count_with_term)) if doc_count_with_term > 0 else 0

# Building the document-term matrix by using the tf-idf weights.
docTermMatrix = []
for doc in cleaned_documents:
    tfidf_row = []
    for term in terms:
        tf = calculate_tf(term, doc)
        idf = calculate_idf(term, cleaned_documents)
        tfidf_row.append(tf * idf)
    docTermMatrix.append(tfidf_row)

# Printing the matrix with documents as rows and terms as columns in the specified order
# Printing header (terms as columns)
print(f"{'Doc':<10}", end="")
for term in terms:
    print(f"{term:<10}", end="")
print()

# Printing each document's row with corresponding TF-IDF values
for i, doc in enumerate(documents):
    print(f"Doc{i+1:<10}", end="")  # Print Doc1, Doc2, Doc3, etc.
    for tfidf_value in docTermMatrix[i]:
        print(f"{tfidf_value:<10.4f}", end="")
    print()

