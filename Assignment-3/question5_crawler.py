import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["assignment"]
pages_collection = db["pages"]

# Initialize frontier with the CS home page URL
frontier = ["https://www.cpp.edu/sci/computer-science/"]
visited = set()
target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

# Function to retrieve and parse HTML content
def retrieve_html(url):
    try:
        response = urllib.request.urlopen(url)
        if "html" in response.getheader("Content-Type"):
            return response.read()
    except Exception as e:
        print(f"Failed to retrieve {url}: {e}")
    return None

# Function to store the page content in MongoDB
def store_page(url, html):
    if html:
        pages_collection.insert_one({"url": url, "html": html.decode("utf-8")})

# Check if the target page is found
def is_target_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find("h1", class_="cpp-h1") and "Permanent Faculty" in soup.h1.text

# Main crawling loop
while frontier:
    url = frontier.pop(0)
    if url in visited:
        continue
    visited.add(url)
    
    html = retrieve_html(url)
    if not html:
        continue
    
    store_page(url, html)
    
    if is_target_page(html):
        print(f"Target page found: {url}")
        break
    
    # Parse and add unvisited URLs to the frontier
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all("a", href=True):
        link_url = urllib.parse.urljoin(url, link["href"])
        if link_url.startswith("https://www.cpp.edu") and link_url not in visited:
            frontier.append(link_url)
