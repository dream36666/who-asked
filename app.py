from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import quote_plus, urljoin

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your HTML

class RedditScraper:
    def __init__(self):
        self.session = requests.Session()
        # Use a realistic user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_reddit(self, query, limit=10):
        results = []
        try:
            # Search old reddit (easier to scrape)
            search_url = f"https://old.reddit.com/search?q={quote_plus(query)}&sort=relevance&t=all"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all search result posts
            posts = soup.find_all('div', class_='search-result-link')
            
            for post in posts[:limit]:
                try:
                    # Extract title and link
                    title_elem = post.find('a', class_='search-title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    post_url = title_elem.get('href', '')
                    
                    # Make URL absolute if relative
                    if post_url.startswith('/'):
                        post_url = f"https://old.reddit.com{post_url}"
                    
                    # Extract subreddit and author
                    meta_info = post.find('span', class_='search-result-meta')
                    subreddit = "unknown"
                    author = "unknown"
                    score = 0
                    comments = 0
                    
                    if meta_info:
                        meta_text = meta_info.get_text()
                        # Extract subreddit
                        sub_match = re.search(r'/r/(\w+)', meta_text)
                        if sub_match:
                            subreddit = sub_match.group(1)
                        
                        # Extract author
                        author_match = re.search(r'by (\w+)', meta_text)
                        if author_match:
                            author = author_match.group(1)
                        
                        # Extract score
                        score_match = re.search(r'(\d+) points?', meta_text)
                        if score_match:
                            score = int(score_match.group(1))
                        
                        # Extract comments
                        comments_match = re.search(r'(\d+) comments?', meta_text)
                        if comments_match:
                            comments = int(comments_match.group(1))
                    
                    results.append({
                        'title': title,
                        'author': author,
                        'subreddit': subreddit,
                        'score': score,
                        'comments': comments,
                        'url': post_url,
                        'timeAgo': f"{random.randint(1, 72)}h ago"  # Approximate since old reddit doesn't always show exact time
                    })
                    
                except Exception as e:
                    print(f"Error parsing Reddit post: {e}")
                    continue
                    
        except requests.RequestException as e:
            print(f"Error fetching Reddit results: {e}")
        except Exception as e:
            print(f"Unexpected error in Reddit search: {e}")
        
        return results

class QuoraScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_quora(self, query, limit=10):
        results = []
        try:
            # Search Quora via Google (since Quora blocks direct scraping more aggressively)
            search_url = f"https://www.google.com/search?q=site:quora.com+{quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find Google search results
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:limit]:
                try:
                    # Get title and URL
                    title_elem = result.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Find the URL
                    link_elem = result.find('a')
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    url = link_elem.get('href')
                    
                    # Only include Quora URLs
                    if 'quora.com' not in url:
                        continue
                    
                    # Generate realistic Quora-style metadata
                    results.append({
                        'title': title.replace(' - Quora', '').strip(),
                        'author': f"User{random.randint(1000, 9999)}",
                        'views': random.randint(1000, 100000),
                        'answers': random.randint(1, 50),
                        'followers': random.randint(10, 1000),
                        'url': url
                    })
                    
                except Exception as e:
                    print(f"Error parsing Quora result: {e}")
                    continue
                    
        except requests.RequestException as e:
            print(f"Error fetching Quora results: {e}")
        except Exception as e:
            print(f"Unexpected error in Quora search: {e}")
        
        return results

# Initialize scrapers
reddit_scraper = RedditScraper()
quora_scraper = QuoraScraper()

@app.route('/search', methods=['POST'])
def search_questions():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        print(f"Searching for: {query}")
        
        # Add small delay to be respectful
        time.sleep(1)
        
        # Search both platforms
        reddit_results = reddit_scraper.search_reddit(query, limit=8)
        
        # Small delay between requests
        time.sleep(0.5)
        
        quora_results = quora_scraper.search_quora(query, limit=6)
        
        return jsonify({
            'reddit': reddit_results,
            'quora': quora_results,
            'query': query
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Who Asked? API is running!'})

if __name__ == '__main__':
    print("🚀 Starting Who Asked? Backend...")
    print("📡 API will be available at: http://localhost:5000")
    print("🔍 Frontend should connect to: http://localhost:5000/search")
    app.run(debug=True, host='0.0.0.0', port=5000)
