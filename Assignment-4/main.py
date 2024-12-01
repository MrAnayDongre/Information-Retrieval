import re
import math
from pymongo import MongoClient
from typing import List, Dict, Any

class SearchEngine:
    def __init__(self):
        # MongoDB connection
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['search_engine_db']
        
        # Clear existing collections
        self.db['terms'].drop()
        self.db['documents'].drop()
        
        # Initialize collections
        self.terms_collection = self.db['terms']
        self.documents_collection = self.db['documents']
        
        # Documents to be indexed
        self.documents = [
            "After the medication, headache and nausea were reported by the patient.",
            "The patient reported nausea and dizziness caused by the medication.",
            "Headache and dizziness are common effects of this medication.",
            "The medication caused a headache and nausea, but no dizziness was reported."
        ]
        
        # Vocabulary tracking
        self.vocabulary = {}
    
    def preprocess_text(self, text: str) -> List[str]:
        """Remove punctuation and lowercase words"""
        text = re.sub(r'[^\w\s]', '', text.lower())
        return text.split()
    
    def generate_ngrams(self, tokens: List[str]) -> List[str]:
        """Generate unigrams, bigrams, and trigrams"""
        # Unigrams
        ngrams = tokens.copy()
        
        # Bigrams
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)]
        
        # Trigrams
        trigrams = [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" 
                    for i in range(len(tokens)-2)]
        
        return ngrams + bigrams + trigrams
    
    def index_documents(self):
        """Create inverted index in MongoDB"""
        # Track term frequencies across all documents
        term_doc_freq = {}
        
        # First pass: count document frequencies
        for doc_id, doc_content in enumerate(self.documents, 1):
            # Preprocess and tokenize
            tokens = self.preprocess_text(doc_content)
            ngrams = self.generate_ngrams(tokens)
            
            # Count document frequencies
            unique_terms = set(ngrams)
            for term in unique_terms:
                if term not in term_doc_freq:
                    term_doc_freq[term] = 0
                term_doc_freq[term] += 1
        
        # Second pass: index documents with TF-IDF
        for doc_id, doc_content in enumerate(self.documents, 1):
            # Preprocess and tokenize
            tokens = self.preprocess_text(doc_content)
            ngrams = self.generate_ngrams(tokens)
            
            # Calculate term frequencies
            term_freq = {}
            for term in ngrams:
                term_freq[term] = term_freq.get(term, 0) + 1
            
            # Insert document
            self.documents_collection.insert_one({
                '_id': doc_id,
                'content': doc_content
            })
            
            # Calculate and store TF-IDF
            for term, freq in term_freq.items():
                # TF: term frequency
                tf = 1 + math.log(freq)
                
                # IDF: inverse document frequency
                idf = math.log(len(self.documents) / (term_doc_freq[term] + 1)) + 1
                
                # TF-IDF
                tfidf = tf * idf
                
                # Assign unique position in vocabulary
                if term not in self.vocabulary:
                    self.vocabulary[term] = len(self.vocabulary)
                
                # Update terms collection
                self.terms_collection.update_one(
                    {'_id': term},
                    {'$addToSet': {'docs': {
                        'doc_id': doc_id, 
                        'tf_idf': tfidf,
                        'pos': self.vocabulary[term]
                    }}},
                    upsert=True
                )
    
    def vector_space_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform vector space model search"""
        # Preprocess query
        query_tokens = self.preprocess_text(query)
        query_ngrams = self.generate_ngrams(query_tokens)
        
        # Find matching documents
        matching_doc_ids = set()
        for term in query_ngrams:
            term_record = self.terms_collection.find_one({'_id': term})
            if term_record:
                matching_doc_ids.update(
                    doc['doc_id'] for doc in term_record.get('docs', [])
                )
        
        # Calculate scores for matching documents
        results = []
        for doc_id in matching_doc_ids:
            doc = self.documents_collection.find_one({'_id': doc_id})
            
            # Compute document vector
            doc_vector = {}
            doc_tokens = self.preprocess_text(doc['content'])
            doc_ngrams = self.generate_ngrams(doc_tokens)
            
            # Get TF-IDF for document terms
            for term in set(doc_ngrams):
                term_record = self.terms_collection.find_one({'_id': term})
                if term_record:
                    for doc_term in term_record.get('docs', []):
                        if doc_term['doc_id'] == doc_id:
                            doc_vector[term] = doc_term['tf_idf']
                            break
            
            # Query vector
            query_vector = {}
            for term in query_ngrams:
                term_record = self.terms_collection.find_one({'_id': term})
                if term_record:
                    for doc_term in term_record.get('docs', []):
                        # Use query term position in vocabulary
                        query_vector[term] = 1.0
            
            # Cosine similarity calculation
            numerator = sum(
                query_vector.get(term, 0) * doc_vector.get(term, 0) 
                for term in set(list(query_vector.keys()) + list(doc_vector.keys()))
            )
            
            query_norm = math.sqrt(sum(1**2 for _ in query_vector))
            doc_norm = math.sqrt(sum(v**2 for v in doc_vector.values()))
            
            if query_norm * doc_norm > 0:
                cosine_sim = numerator / (query_norm * doc_norm)
                results.append({
                    'content': doc['content'],
                    'score': round(cosine_sim, 2)
                })
        
        # Sort results by score in descending order
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def run_queries(self, queries):
        """Execute and print results for all queries"""
        for query in queries:
            print(f"Query: {query}")
            results = self.vector_space_search(query)
            for result in results:
                print(f'"{result["content"]}", {result["score"]}')
            print()

def main():
    # Initialize search engine
    search_engine = SearchEngine()
    
    # Index documents
    search_engine.index_documents()
    
    # Queries from assignment
    queries = [
        "nausea and dizziness",
        "effects",
        "nausea was reported", 
        "dizziness",
        "the medication"
    ]
    
    # Run queries
    search_engine.run_queries(queries)

if __name__ == "__main__":
    main()