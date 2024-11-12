import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["assignment"]
pages_collection = db["pages"]
professors_collection = db["professors"]

# Define URLs
start_url = "https://www.cpp.edu/sci/computer-science/"
target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

# Initialize the frontier and visited set
frontier = [start_url]
visited = set()

def retrieve_html(url):
    try:
        response = urllib.request.urlopen(url)
        if "html" in response.getheader("Content-Type"):
            return response.read()
    except Exception as e:
        print(f"Failed to retrieve {url}: {e}")
    return None

def store_page(url, html):
    if html and not pages_collection.find_one({"url": url}):
        pages_collection.insert_one({"url": url, "html": html.decode("utf-8")})
        print(f"Stored page: {url}")

def parse_professor_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    professors = soup.find_all("div", class_="clearfix")
    
    for professor_info in professors:
        # Extract name
        name = None
        name_tag = professor_info.find("h2")
        if name_tag:
            name = name_tag.get_text(strip=True)
        
        # Extract title - multiple approaches
        title = None
        # Try first approach - strong tag
        title_tag = professor_info.find("strong", text=lambda t: t and "Title:" in t)
        if title_tag and title_tag.next_sibling:
            title = title_tag.next_sibling.strip()
        # Try second approach - text after Title:
        if not title:
            for p in professor_info.find_all("p"):
                text = p.get_text()
                if "Title:" in text:
                    title = text.split("Title:")[1].strip()
                    break

        # Extract office - multiple approaches
        office = None
        office_tag = professor_info.find("strong", text=lambda t: t and "Office:" in t)
        if office_tag and office_tag.next_sibling:
            office = office_tag.next_sibling.strip()
        if not office:
            for p in professor_info.find_all("p"):
                text = p.get_text()
                if "Office:" in text:
                    office = text.split("Office:")[1].strip()
                    break

        # Extract phone - multiple approaches
        phone = None
        phone_tag = professor_info.find("strong", text=lambda t: t and "Phone:" in t)
        if phone_tag and phone_tag.next_sibling:
            phone = phone_tag.next_sibling.strip()
        if not phone:
            for p in professor_info.find_all("p"):
                text = p.get_text()
                if "Phone:" in text:
                    phone = text.split("Phone:")[1].strip()
                    # Clean up incomplete phone numbers
                    if phone and phone.strip() == "(909) 869-":
                        phone = None
                    break

        # Extract email - multiple approaches
        email = None
        # Try first approach - mailto link
        email_tag = professor_info.find("a", href=lambda h: h and "mailto:" in h)
        if email_tag:
            email = email_tag.get_text(strip=True)
            if not email:  # If text is empty, try getting from href
                email = email_tag["href"].replace("mailto:", "")
        # Try second approach - text after Email:
        if not email:
            for p in professor_info.find_all("p"):
                text = p.get_text()
                if "Email:" in text:
                    email = text.split("Email:")[1].strip()
                    break

        # Extract website - multiple approaches
        website = None
        # Try first approach - Web: link
        website_tag = professor_info.find("a", text=lambda t: t and ("Web:" in t or "Website" in t))
        if website_tag and "mailto:" not in website_tag.get("href", ""):
            website = website_tag["href"]
        # Try second approach - any non-mailto link after website text
        if not website:
            for p in professor_info.find_all("p"):
                if "Website:" in p.get_text() or "Web:" in p.get_text():
                    web_link = p.find("a", href=lambda h: h and "mailto:" not in h)
                    if web_link:
                        website = web_link["href"]
                        break

        # Prepare the professor data dictionary
        professor_data = {
            "name": name,
            "title": title,
            "office": office,
            "phone": phone,
            "email": email,
            "website": website
        }

        # Only insert if we have at least name and email
        if name and email and not professors_collection.find_one({"name": name, "email": email}):
            professors_collection.insert_one(professor_data)
            print(f"Stored professor: {name}")
            print(f"Data: {professor_data}")

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
    
    if url == target_url:
        print(f"Target page found: {url}")
        parse_professor_data(html)
        break

    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all("a", href=True):
        link_url = urllib.parse.urljoin(url, link["href"])
        if link_url.startswith("https://www.cpp.edu/sci/computer-science") and link_url not in visited:
            frontier.append(link_url)

print("Crawling completed!")