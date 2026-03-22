from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random
import pandas as pd
import ast
import os
import re

app = Flask(__name__)

APP_NAME = "Article Recommendation System"
VERSION = "2.0"

# Global variable to store articles data
articles_data = []

def load_data_from_csv():
    """Load articles from medium_articles.csv file"""
    global articles_data
    
    # Check if CSV file exists
    if not os.path.exists("medium_articles.csv"):
        print("❌ ERROR: medium_articles.csv file not found!")
        print("   Creating sample data for testing...")
        return create_sample_data()
    
    try:
        print("📂 Loading articles from medium_articles.csv...")
        df = pd.read_csv("medium_articles.csv")
        print(f"   ✓ Loaded {len(df)} articles")
        print(f"   ✓ Columns found: {list(df.columns)}")
        
        # Convert DataFrame to list of dictionaries
        articles = []
        
        for idx, row in df.iterrows():
            # Get title
            title = "Untitled"
            if 'title' in df.columns and pd.notna(row['title']):
                title = str(row['title'])
            
            # Get content/text
            content = "No content available"
            if 'text' in df.columns and pd.notna(row['text']):
                content = str(row['text'])
            elif 'content' in df.columns and pd.notna(row['content']):
                content = str(row['content'])
            
            # Get tags
            tags = []
            if 'tags' in df.columns and pd.notna(row['tags']):
                try:
                    tag_value = str(row['tags'])
                    if tag_value.startswith('['):
                        tags = ast.literal_eval(tag_value)
                    elif ',' in tag_value:
                        tags = [t.strip() for t in tag_value.split(',')]
                    else:
                        tags = [tag_value]
                except:
                    tags = []
            
            # Get date
            date = "2024-01-01"
            if 'timestamp' in df.columns and pd.notna(row['timestamp']):
                date = str(row['timestamp'])[:10]
            
            # Get author
            author = "Unknown"
            if 'authors' in df.columns and pd.notna(row['authors']):
                author = str(row['authors'])
            
            # Get URL
            url = "#"
            if 'url' in df.columns and pd.notna(row['url']):
                url = str(row['url'])
            
            # Calculate reading time (approx 200 words per minute)
            reading_time = max(1, len(content) // 500)
            
            article = {
                'id': idx,
                'title': title,
                'content': content,
                'reading_time': reading_time,
                'tags': tags,
                'date': date,
                'author': author,
                'views': random.randint(100, 10000),
                'url': url
            }
            articles.append(article)
        
        articles_data = articles
        print(f"   ✓ Successfully loaded {len(articles_data)} articles")
        print(f"   ✓ First article title: {articles_data[0]['title'][:50] if articles_data else 'None'}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Create sample data for testing if CSV not found"""
    global articles_data
    print("📊 Creating sample data for testing...")
    
    articles = []
    sample_articles = [
        {
            'title': 'Python Programming for Beginners',
            'content': 'Python is a powerful programming language that is easy to learn. This article covers variables, loops, functions, and object-oriented programming.',
            'tags': ['python', 'programming', 'beginners']
        },
        {
            'title': 'Advanced Python Techniques',
            'content': 'Learn advanced Python concepts including decorators, generators, context managers, and multithreading for better performance.',
            'tags': ['python', 'advanced', 'programming']
        },
        {
            'title': 'Data Science with Python',
            'content': 'Explore data science using Python libraries like pandas, numpy, and matplotlib for data analysis and visualization.',
            'tags': ['datascience', 'python', 'analytics']
        },
        {
            'title': 'Machine Learning Fundamentals',
            'content': 'Introduction to machine learning concepts including supervised learning, unsupervised learning, and neural networks.',
            'tags': ['machinelearning', 'ai', 'algorithms']
        },
        {
            'title': 'Deep Learning Explained',
            'content': 'Deep learning and neural networks tutorial covering CNNs, RNNs, and transformers for advanced AI applications.',
            'tags': ['deeplearning', 'ai', 'neuralnetworks']
        },
        {
            'title': 'Web Development with Flask',
            'content': 'Build web applications using Flask framework. Learn routing, templates, and database integration with SQLAlchemy.',
            'tags': ['flask', 'webdev', 'python']
        },
        {
            'title': 'Cloud Computing Guide',
            'content': 'Comprehensive guide to cloud computing platforms AWS, Azure, and Google Cloud Platform for deploying applications.',
            'tags': ['cloud', 'aws', 'azure', 'devops']
        },
        {
            'title': 'Cybersecurity Basics',
            'content': 'Learn essential cybersecurity concepts including encryption, authentication, firewalls, and security best practices.',
            'tags': ['security', 'cybersecurity', 'privacy']
        },
        {
            'title': 'DevOps Practices',
            'content': 'DevOps principles and practices including CI/CD, Docker, Kubernetes, and infrastructure as code with Terraform.',
            'tags': ['devops', 'cicd', 'docker', 'kubernetes']
        }
    ]
    
    for idx, article_data in enumerate(sample_articles):
        article = {
            'id': idx,
            'title': article_data['title'],
            'content': article_data['content'],
            'reading_time': random.randint(5, 15),
            'tags': article_data['tags'],
            'date': f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            'author': f"Author {idx+1}",
            'views': random.randint(100, 5000),
            'url': "#"
        }
        articles.append(article)
    
    articles_data = articles
    print(f"   ✓ Created {len(articles_data)} sample articles")
    return True

# Helper function to get all unique tags with counts
def get_all_tags():
    """Get all unique tags with counts"""
    tag_counts = {}
    for article in articles_data:
        for tag in article['tags']:
            if tag and str(tag).strip():
                tag_clean = str(tag).strip().lower()
                tag_counts[tag_clean] = tag_counts.get(tag_clean, 0) + 1
    
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_tags

# Helper function to get recommendations
def get_recommendations(current_article_id, limit=3):
    """Get article recommendations based on tag similarity"""
    current_article = None
    for article in articles_data:
        if article['id'] == current_article_id:
            current_article = article
            break
    
    if not current_article:
        return []
    
    recommendations = []
    current_tags = set([t.lower() for t in current_article['tags']])
    
    for article in articles_data:
        if article['id'] != current_article_id:
            article_tags = set([t.lower() for t in article['tags']])
            matching_tags = len(current_tags & article_tags)
            score = matching_tags * 10 + (article['views'] / 1000)
            recommendations.append({'article': article, 'score': score})
    
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return [rec['article'] for rec in recommendations[:limit]]

# SEARCH FUNCTION - This is the key part for search
def search_articles(query=None, tag=None):
    """Search articles by title/content or filter by tag"""
    results = []
    
    if tag:
        # Search by tag
        tag_lower = tag.lower()
        for article in articles_data:
            article_tags = [t.lower() for t in article['tags']]
            if tag_lower in article_tags:
                results.append(article)
    elif query:
        # Search by text in title and content
        query_lower = query.lower()
        for article in articles_data:
            # Check if query appears in title OR content
            if (query_lower in article['title'].lower() or 
                query_lower in article['content'].lower()):
                results.append(article)
    
    return results

# ============================================
# LOAD DATA ON STARTUP
# ============================================
print("\n" + "="*60)
print(f"📚 {APP_NAME} v{VERSION}")
print("="*60)

# Load data from CSV
if load_data_from_csv():
    print(f"\n✅ SYSTEM INITIALIZED SUCCESSFULLY!")
    print(f"📊 Total articles: {len(articles_data)}")
    print(f"🏷️ Unique tags: {len(get_all_tags())}")
    print("="*60)
else:
    print("\n⚠️ WARNING: Could not load articles!")
    print("="*60)

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/')
def home():
    """Home page with latest articles"""
    if not articles_data:
        return render_template('error.html', 
                             message="No articles found. Please check your database file.",
                             app_name=APP_NAME, 
                             version=VERSION)
    
    try:
        latest_articles = articles_data[:min(8, len(articles_data))]
        popular_tags = get_all_tags()[:12]
        random_count = min(3, len(articles_data))
        random_articles = random.sample(articles_data, random_count) if random_count > 0 else []
        
        return render_template('index.html', 
                             articles=latest_articles,
                             popular_tags=popular_tags,
                             random_articles=random_articles,
                             total_articles=len(articles_data),
                             total_tags=len(get_all_tags()),
                             app_name=APP_NAME,
                             version=VERSION)
    except Exception as e:
        print(f"Error in home route: {e}")
        return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

@app.route('/article/<int:article_id>')
def view_article(article_id):
    """Article detail page with recommendations"""
    if not articles_data:
        return render_template('error.html', message="No articles found", app_name=APP_NAME, version=VERSION)
    
    try:
        found_article = None
        for article in articles_data:
            if article['id'] == article_id:
                found_article = article
                break
        
        if found_article is None:
            return render_template('404.html', message="Article not found", app_name=APP_NAME, version=VERSION), 404
        
        found_article['views'] = found_article.get('views', 0) + 1
        recommendations = get_recommendations(article_id, limit=3)
        
        return render_template('article.html', 
                             article=found_article,
                             recommendations=recommendations,
                             app_name=APP_NAME,
                             version=VERSION)
    except Exception as e:
        print(f"Error in article route: {e}")
        return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

@app.route('/search')
def search():
    """Search results page - This handles the search functionality"""
    if not articles_data:
        return render_template('error.html', message="No articles found", app_name=APP_NAME, version=VERSION)
    
    try:
        # Get search parameters from URL
        query = request.args.get('q', '').strip()
        tag = request.args.get('tag', '').strip()
        
        print(f"\n🔍 SEARCH REQUEST:")
        print(f"   Query: '{query}'")
        print(f"   Tag: '{tag}'")
        
        results = []
        search_type = ""
        
        if tag:
            # Search by tag
            results = search_articles(tag=tag)
            search_type = f"Tag: #{tag}"
            print(f"   Searching by tag: {tag}")
        elif query:
            # Search by text
            results = search_articles(query=query)
            search_type = f"Search: '{query}'"
            print(f"   Searching for: {query}")
        else:
            # Show all articles if no search parameter
            results = articles_data
            search_type = "All Articles"
            print(f"   Showing all articles")
        
        print(f"   Found {len(results)} results")
        
        # Show first few results for debugging
        for i, result in enumerate(results[:3]):
            print(f"   Result {i+1}: {result['title'][:50]}")
        
        # Get popular tags for sidebar
        popular_tags = get_all_tags()[:12]
        
        return render_template('search.html',
                             results=results,
                             search_type=search_type,
                             total_results=len(results),
                             popular_tags=popular_tags,
                             app_name=APP_NAME,
                             version=VERSION)
    except Exception as e:
        print(f"❌ Error in search route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

@app.route('/tags')
def tags_page():
    """Browse all tags"""
    if not articles_data:
        return render_template('error.html', message="No articles found", app_name=APP_NAME, version=VERSION)
    
    try:
        all_tags = get_all_tags()
        return render_template('tags.html', 
                             tags=all_tags, 
                             total_tags=len(all_tags),
                             app_name=APP_NAME,
                             version=VERSION)
    except Exception as e:
        print(f"Error in tags route: {e}")
        return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

@app.route('/browse')
def browse():
    """Browse all articles with pagination"""
    if not articles_data:
        return render_template('error.html', message="No articles found", app_name=APP_NAME, version=VERSION)
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 6
        
        total = len(articles_data)
        start = (page - 1) * per_page
        end = min(start + per_page, total)
        articles = articles_data[start:end]
        
        return render_template('browse.html',
                             articles=articles,
                             page=page,
                             total=total,
                             per_page=per_page,
                             total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
                             app_name=APP_NAME,
                             version=VERSION)
    except Exception as e:
        print(f"Error in browse route: {e}")
        return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html',
                         app_name=APP_NAME,
                         version=VERSION,
                         total_articles=len(articles_data) if articles_data else 0,
                         total_tags=len(get_all_tags()) if articles_data else 0)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app_name': APP_NAME,
        'version': VERSION,
        'timestamp': datetime.now().isoformat(),
        'articles_loaded': len(articles_data) if articles_data else 0,
        'total_tags': len(get_all_tags()) if articles_data else 0
    })

# Test search endpoint
@app.route('/test-search')
def test_search():
    """Test search functionality"""
    test_word = request.args.get('word', 'python')
    results = search_articles(query=test_word)
    return jsonify({
        'search_word': test_word,
        'results_count': len(results),
        'results': [{'title': r['title'], 'content_preview': r['content'][:100]} for r in results]
    })

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message="Page not found", app_name=APP_NAME, version=VERSION), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', message="Internal server error", app_name=APP_NAME, version=VERSION), 500

# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING FLASK SERVER")
    print("="*60)
    print("📍 Open your browser and go to:")
    print("📍 http://127.0.0.1:5000")
    print("\n📝 SEARCH EXAMPLES:")
    print("   - Search by word: http://127.0.0.1:5000/search?q=python")
    print("   - Search by tag: http://127.0.0.1:5000/search?tag=machinelearning")
    print("   - Test search: http://127.0.0.1:5000/test-search?word=data")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
















# from flask import Flask, render_template, request, jsonify
# from datetime import datetime
# import random
# import pandas as pd
# import ast
# import os
# import re

# app = Flask(__name__)

# APP_NAME = "Article Recommendation System"
# VERSION = "2.0"

# # Global variable to store articles data
# articles_data = []

# def load_data_from_csv():
#     """Load articles from medium_articles.csv file"""
#     global articles_data
    
#     # Check if CSV file exists
#     if not os.path.exists("medium_articles.csv"):
#         print("❌ ERROR: medium_articles.csv file not found!")
#         print("   Creating sample data for testing...")
#         return create_sample_data()
    
#     try:
#         print("📂 Loading articles from medium_articles.csv...")
#         df = pd.read_csv("medium_articles.csv")
#         print(f"   ✓ Loaded {len(df)} articles")
#         print(f"   ✓ Columns found: {list(df.columns)}")
        
#         # Convert DataFrame to list of dictionaries
#         articles = []
        
#         for idx, row in df.iterrows():
#             # Process tags - try different possible column names
#             tags = []
#             tag_column = None
#             if 'tags' in df.columns:
#                 tag_column = 'tags'
#             elif 'tag' in df.columns:
#                 tag_column = 'tag'
#             elif 'keywords' in df.columns:
#                 tag_column = 'keywords'
            
#             if tag_column and pd.notna(row[tag_column]):
#                 try:
#                     tag_value = str(row[tag_column])
#                     if tag_value.startswith('['):
#                         tags = ast.literal_eval(tag_value)
#                     elif ',' in tag_value:
#                         tags = [t.strip() for t in tag_value.split(',')]
#                     else:
#                         tags = [tag_value]
#                 except:
#                     tags = []
            
#             # Process title - try different possible column names
#             title = "Untitled"
#             if 'title' in df.columns and pd.notna(row['title']):
#                 title = str(row['title'])
#             elif 'headline' in df.columns and pd.notna(row['headline']):
#                 title = str(row['headline'])
#             elif 'name' in df.columns and pd.notna(row['name']):
#                 title = str(row['name'])
            
#             # Process content - try different possible column names
#             content = "No content available"
#             if 'text' in df.columns and pd.notna(row['text']):
#                 content = str(row['text'])
#             elif 'content' in df.columns and pd.notna(row['content']):
#                 content = str(row['content'])
#             elif 'body' in df.columns and pd.notna(row['body']):
#                 content = str(row['body'])
            
#             # Process date - try different possible column names
#             date = "2024-01-01"
#             if 'timestamp' in df.columns and pd.notna(row['timestamp']):
#                 date = str(row['timestamp'])[:10]
#             elif 'date' in df.columns and pd.notna(row['date']):
#                 date = str(row['date'])[:10]
#             elif 'published' in df.columns and pd.notna(row['published']):
#                 date = str(row['published'])[:10]
            
#             # Process author - try different possible column names
#             author = "Unknown"
#             if 'authors' in df.columns and pd.notna(row['authors']):
#                 author = str(row['authors'])
#             elif 'author' in df.columns and pd.notna(row['author']):
#                 author = str(row['author'])
            
#             # Process URL
#             url = "#"
#             if 'url' in df.columns and pd.notna(row['url']):
#                 url = str(row['url'])
            
#             # Calculate reading time (approx 200 words per minute)
#             reading_time = max(1, len(content) // 500)
            
#             # Create article dictionary
#             article = {
#                 'id': idx,
#                 'title': title,
#                 'content': content,
#                 'reading_time': reading_time,
#                 'tags': tags,
#                 'date': date,
#                 'author': author,
#                 'views': random.randint(100, 10000),
#                 'url': url
#             }
#             articles.append(article)
        
#         articles_data = articles
#         print(f"   ✓ Successfully loaded {len(articles_data)} articles")
#         print(f"   ✓ Sample tags: {articles_data[0]['tags'] if articles_data else 'None'}")
#         return True
        
#     except Exception as e:
#         print(f"❌ Error loading CSV: {e}")
#         import traceback
#         traceback.print_exc()
#         return False

# def create_sample_data():
#     """Create sample data for testing if CSV not found"""
#     global articles_data
#     print("📊 Creating sample data for testing...")
    
#     articles = []
#     sample_topics = [
#         "Python Programming", "Data Science", "Machine Learning", 
#         "Web Development", "Artificial Intelligence", "Cloud Computing",
#         "Cybersecurity", "DevOps", "Blockchain", "IoT"
#     ]
    
#     for i in range(20):
#         topic = sample_topics[i % len(sample_topics)]
#         article = {
#             'id': i,
#             'title': f"{topic} Complete Guide 2024",
#             'content': f"This is a comprehensive guide about {topic}. You will learn everything from basics to advanced concepts. Perfect for beginners and experienced professionals. We cover all essential topics with practical examples and real-world applications. By the end of this guide, you'll have a solid understanding of {topic} and be able to apply it in your projects.",
#             'reading_time': random.randint(5, 15),
#             'tags': [topic.lower().replace(' ', ''), 'tutorial', 'guide'],
#             'date': f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
#             'author': f"Author {i+1}",
#             'views': random.randint(100, 5000),
#             'url': "#"
#         }
#         articles.append(article)
    
#     articles_data = articles
#     print(f"   ✓ Created {len(articles_data)} sample articles")
#     return True

# # Helper function to get all unique tags with counts
# def get_all_tags():
#     """Get all unique tags with counts"""
#     tag_counts = {}
#     for article in articles_data:
#         for tag in article['tags']:
#             if tag and str(tag).strip():
#                 tag_clean = str(tag).strip().lower()
#                 tag_counts[tag_clean] = tag_counts.get(tag_clean, 0) + 1
    
#     # Sort by count
#     sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
#     return sorted_tags

# # Helper function to get recommendations based on tags
# def get_recommendations(current_article_id, limit=3):
#     """Get article recommendations based on tag similarity"""
#     current_article = None
#     for article in articles_data:
#         if article['id'] == current_article_id:
#             current_article = article
#             break
    
#     if not current_article:
#         return []
    
#     # Calculate similarity score based on matching tags
#     recommendations = []
#     current_tags = set([t.lower() for t in current_article['tags']])
    
#     for article in articles_data:
#         if article['id'] != current_article_id:
#             # Count matching tags
#             article_tags = set([t.lower() for t in article['tags']])
#             matching_tags = len(current_tags & article_tags)
            
#             # Calculate score based on tag matches and views
#             score = matching_tags * 10 + (article['views'] / 1000)
            
#             recommendations.append({
#                 'article': article,
#                 'score': score
#             })
    
#     # Sort by score and return top recommendations
#     recommendations.sort(key=lambda x: x['score'], reverse=True)
#     return [rec['article'] for rec in recommendations[:limit]]

# # Helper function to search articles
# def search_articles(query=None, tag=None):
#     """Search articles by title/content or filter by tag"""
#     results = []
    
#     print(f"🔍 Searching - Query: '{query}', Tag: '{tag}'")  # Debug print
    
#     for article in articles_data:
#         if tag:
#             # Filter by tag
#             tag_lower = tag.lower()
#             article_tags_lower = [t.lower() for t in article['tags']]
#             if tag_lower in article_tags_lower:
#                 results.append(article)
#                 print(f"   ✓ Found by tag: {article['title']}")  # Debug print
#         elif query:
#             # Search in title and content
#             query_lower = query.lower()
#             title_match = query_lower in article['title'].lower()
#             content_match = query_lower in article['content'].lower()
            
#             if title_match or content_match:
#                 results.append(article)
#                 print(f"   ✓ Found by search: {article['title']}")  # Debug print
    
#     print(f"   📊 Search returned {len(results)} results")  # Debug print
#     return results

# # ============================================
# # LOAD DATA ON STARTUP
# # ============================================
# print("\n" + "="*60)
# print(f"📚 {APP_NAME} v{VERSION}")
# print("="*60)

# # Load data from CSV
# if load_data_from_csv():
#     print(f"\n✅ SYSTEM INITIALIZED SUCCESSFULLY!")
#     print(f"📊 Total articles: {len(articles_data)}")
#     print(f"🏷️ Unique tags: {len(get_all_tags())}")
#     if articles_data:
#         print(f"📝 Sample article: {articles_data[0]['title'][:50]}...")
#     print("="*60)
# else:
#     print("\n⚠️ WARNING: Could not load articles!")
#     print("="*60)

# # ============================================
# # FLASK ROUTES
# # ============================================

# @app.route('/')
# def home():
#     """Home page with latest articles"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found. Please check your database file.",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         # Get latest articles (first 8 or fewer)
#         latest_articles = articles_data[:min(8, len(articles_data))]
        
#         # Get popular tags
#         popular_tags = get_all_tags()[:12]
        
#         # Get some random articles for discovery
#         random_count = min(3, len(articles_data))
#         random_articles = random.sample(articles_data, random_count) if random_count > 0 else []
        
#         return render_template('index.html', 
#                              articles=latest_articles,
#                              popular_tags=popular_tags,
#                              random_articles=random_articles,
#                              total_articles=len(articles_data),
#                              total_tags=len(get_all_tags()),
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in home route: {e}")
#         import traceback
#         traceback.print_exc()
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/article/<int:article_id>')
# def view_article(article_id):
#     """Article detail page with recommendations"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         # Find the article
#         found_article = None
#         for article in articles_data:
#             if article['id'] == article_id:
#                 found_article = article
#                 break
        
#         if found_article is None:
#             return render_template('404.html', 
#                                  message="Article not found", 
#                                  app_name=APP_NAME, 
#                                  version=VERSION), 404
        
#         # Increment view count
#         found_article['views'] = found_article.get('views', 0) + 1
        
#         # Get recommendations
#         recommendations = get_recommendations(article_id, limit=3)
        
#         return render_template('article.html', 
#                              article=found_article,
#                              recommendations=recommendations,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in article route: {e}")
#         import traceback
#         traceback.print_exc()
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/search')
# def search():
#     """Search results page"""
#     print("\n" + "="*50)
#     print("🔍 SEARCH REQUEST RECEIVED")
#     print("="*50)
    
#     if not articles_data:
#         print("❌ No articles data available")
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         query = request.args.get('q', '').strip()
#         tag = request.args.get('tag', '').strip()
        
#         print(f"📝 Search parameters:")
#         print(f"   Query: '{query}'")
#         print(f"   Tag: '{tag}'")
#         print(f"   Total articles in DB: {len(articles_data)}")
        
#         results = []
#         search_type = ""
        
#         if tag:
#             print(f"🔍 Searching by tag: '{tag}'")
#             results = search_articles(tag=tag)
#             search_type = f"Tag: #{tag}"
#         elif query:
#             print(f"🔍 Searching by query: '{query}'")
#             results = search_articles(query=query)
#             search_type = f"Search: '{query}'"
#         else:
#             print(f"🔍 Showing all articles")
#             results = articles_data
#             search_type = "All Articles"
        
#         print(f"📊 Found {len(results)} results")
        
#         # Get popular tags for sidebar
#         popular_tags = get_all_tags()[:12]
        
#         return render_template('search.html',
#                              results=results,
#                              search_type=search_type,
#                              total_results=len(results),
#                              popular_tags=popular_tags,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"❌ Error in search route: {e}")
#         import traceback
#         traceback.print_exc()
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/tags')
# def tags_page():
#     """Browse all tags"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         all_tags = get_all_tags()
#         return render_template('tags.html', 
#                              tags=all_tags, 
#                              total_tags=len(all_tags),
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in tags route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/browse')
# def browse():
#     """Browse all articles with pagination"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         page = request.args.get('page', 1, type=int)
#         per_page = 6
        
#         total = len(articles_data)
#         start = (page - 1) * per_page
#         end = min(start + per_page, total)
#         articles = articles_data[start:end]
        
#         return render_template('browse.html',
#                              articles=articles,
#                              page=page,
#                              total=total,
#                              per_page=per_page,
#                              total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in browse route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/about')
# def about():
#     """About page"""
#     return render_template('about.html',
#                          app_name=APP_NAME,
#                          version=VERSION,
#                          total_articles=len(articles_data) if articles_data else 0,
#                          total_tags=len(get_all_tags()) if articles_data else 0)

# @app.route('/health')
# def health():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'app_name': APP_NAME,
#         'version': VERSION,
#         'timestamp': datetime.now().isoformat(),
#         'articles_loaded': len(articles_data) if articles_data else 0,
#         'total_tags': len(get_all_tags()) if articles_data else 0,
#         'sample_article': articles_data[0]['title'] if articles_data else None
#     })

# # ============================================
# # API ENDPOINTS
# # ============================================

# @app.route('/api/articles')
# def api_articles():
#     """API endpoint to get all articles"""
#     return jsonify(articles_data)

# @app.route('/api/article/<int:article_id>')
# def api_article(article_id):
#     """API endpoint to get a single article"""
#     for article in articles_data:
#         if article['id'] == article_id:
#             return jsonify(article)
#     return jsonify({'error': 'Article not found'}), 404

# @app.route('/api/recommend/<int:article_id>')
# def api_recommend(article_id):
#     """API endpoint to get recommendations"""
#     recommendations = get_recommendations(article_id, limit=5)
#     return jsonify(recommendations)

# @app.route('/api/tags')
# def api_tags():
#     """API endpoint to get all tags"""
#     all_tags = get_all_tags()
#     return jsonify([{'tag': tag, 'count': count} for tag, count in all_tags])

# @app.route('/api/search')
# def api_search():
#     """API endpoint to search articles"""
#     query = request.args.get('q', '')
#     tag = request.args.get('tag', '')
    
#     if tag:
#         results = search_articles(tag=tag)
#     elif query:
#         results = search_articles(query=query)
#     else:
#         results = articles_data
    
#     return jsonify(results)

# # ============================================
# # DEBUG ROUTE - Check data
# # ============================================

# @app.route('/debug')
# def debug():
#     """Debug endpoint to check data"""
#     return jsonify({
#         'total_articles': len(articles_data),
#         'sample_article': articles_data[0] if articles_data else None,
#         'all_tags': get_all_tags()[:10],
#         'search_test': search_articles(query='python')[:3] if articles_data else []
#     })

# # ============================================
# # ERROR HANDLERS
# # ============================================

# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html', 
#                          message="Page not found", 
#                          app_name=APP_NAME, 
#                          version=VERSION), 404

# @app.errorhandler(500)
# def internal_error(e):
#     return render_template('error.html', 
#                          message="Internal server error", 
#                          app_name=APP_NAME, 
#                          version=VERSION), 500

# # ============================================
# # MAIN ENTRY POINT
# # ============================================
# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("🚀 STARTING FLASK SERVER")
#     print("="*60)
#     print("📍 Open your browser and go to:")
#     print("📍 http://127.0.0.1:5000")
#     print("📍 Debug page: http://127.0.0.1:5000/debug")
#     print("="*60 + "\n")
    
#     app.run(debug=True, host='127.0.0.1', port=5000)











# from flask import Flask, render_template, request, jsonify
# from datetime import datetime
# import random
# import pandas as pd
# import ast
# import os

# app = Flask(__name__)

# APP_NAME = "Article Recommendation System"
# VERSION = "2.0"

# # Global variable to store articles data
# articles_data = []

# def load_data_from_csv():
#     """Load articles from medium_articles.csv file"""
#     global articles_data
    
#     # Check if CSV file exists
#     if not os.path.exists("medium_articles.csv"):
#         print("❌ ERROR: medium_articles.csv file not found!")
#         print("   Please make sure the file is in the current directory")
#         return False
    
#     try:
#         print("📂 Loading articles from medium_articles.csv...")
#         df = pd.read_csv("medium_articles.csv")
#         print(f"   ✓ Loaded {len(df)} articles")
        
#         # Convert DataFrame to list of dictionaries
#         articles = []
        
#         for idx, row in df.iterrows():
#             # Process tags
#             tags = []
#             if 'tags' in df.columns and pd.notna(row['tags']):
#                 try:
#                     if isinstance(row['tags'], str):
#                         if row['tags'].startswith('['):
#                             tags = ast.literal_eval(row['tags'])
#                         else:
#                             tags = [row['tags']]
#                     elif isinstance(row['tags'], list):
#                         tags = row['tags']
#                 except:
#                     tags = []
            
#             # Process title
#             title = row['title'] if 'title' in df.columns and pd.notna(row['title']) else f"Article {idx}"
            
#             # Process content
#             content = row['text'] if 'text' in df.columns and pd.notna(row['text']) else "No content available"
            
#             # Process date
#             date = row['timestamp'][:10] if 'timestamp' in df.columns and pd.notna(row['timestamp']) else "2024-01-01"
            
#             # Process reading time
#             reading_time = max(1, len(str(content)) // 500)  # Approximate reading time
            
#             # Create article dictionary
#             article = {
#                 'id': idx,
#                 'title': str(title),
#                 'content': str(content),
#                 'reading_time': reading_time,
#                 'tags': tags,
#                 'date': str(date)[:10],
#                 'author': row['authors'] if 'authors' in df.columns and pd.notna(row['authors']) else "Unknown",
#                 'views': random.randint(100, 10000),  # Random views for now
#                 'url': row['url'] if 'url' in df.columns and pd.notna(row['url']) else "#"
#             }
#             articles.append(article)
        
#         articles_data = articles
#         print(f"   ✓ Successfully loaded {len(articles_data)} articles")
#         return True
        
#     except Exception as e:
#         print(f"❌ Error loading CSV: {e}")
#         return False

# # Helper function to get all unique tags with counts
# def get_all_tags():
#     """Get all unique tags with counts"""
#     tag_counts = {}
#     for article in articles_data:
#         for tag in article['tags']:
#             if tag:  # Only count non-empty tags
#                 tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
#     # Sort by count
#     sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
#     return sorted_tags

# # Helper function to get recommendations based on tags
# def get_recommendations(current_article_id, limit=3):
#     """Get article recommendations based on tag similarity"""
#     current_article = None
#     for article in articles_data:
#         if article['id'] == current_article_id:
#             current_article = article
#             break
    
#     if not current_article:
#         return []
    
#     # Calculate similarity score based on matching tags
#     recommendations = []
#     current_tags = set(current_article['tags'])
    
#     for article in articles_data:
#         if article['id'] != current_article_id:
#             # Count matching tags
#             article_tags = set(article['tags'])
#             matching_tags = len(current_tags & article_tags)
            
#             # Calculate score based on tag matches and views
#             score = matching_tags * 10 + (article['views'] / 1000)
            
#             recommendations.append({
#                 'article': article,
#                 'score': score
#             })
    
#     # Sort by score and return top recommendations
#     recommendations.sort(key=lambda x: x['score'], reverse=True)
#     return [rec['article'] for rec in recommendations[:limit]]

# # Helper function to search articles
# def search_articles(query=None, tag=None):
#     """Search articles by title/content or filter by tag"""
#     results = []
    
#     for article in articles_data:
#         if tag:
#             # Filter by tag
#             if tag.lower() in [t.lower() for t in article['tags']]:
#                 results.append(article)
#         elif query:
#             # Search in title and content
#             if (query.lower() in article['title'].lower() or 
#                 query.lower() in article['content'].lower()):
#                 results.append(article)
    
#     return results

# # ============================================
# # LOAD DATA ON STARTUP
# # ============================================
# print("\n" + "="*60)
# print(f"📚 {APP_NAME} v{VERSION}")
# print("="*60)

# # Load data from CSV
# if load_data_from_csv():
#     print(f"\n✅ SYSTEM INITIALIZED SUCCESSFULLY!")
#     print(f"📊 Total articles: {len(articles_data)}")
#     print(f"🏷️ Unique tags: {len(get_all_tags())}")
#     total_views = sum(article['views'] for article in articles_data)
#     print(f"👁️ Total views: {total_views:,}")
#     print("="*60)
# else:
#     print("\n⚠️ WARNING: Could not load articles from CSV!")
#     print("📁 Please make sure medium_articles.csv is in the current directory")
#     print("="*60)

# # ============================================
# # FLASK ROUTES
# # ============================================

# @app.route('/')
# def home():
#     """Home page with latest articles"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found. Please check your database file.",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         # Get latest articles (first 8 or fewer)
#         latest_articles = articles_data[:min(8, len(articles_data))]
        
#         # Get popular tags
#         popular_tags = get_all_tags()[:12]
        
#         # Get some random articles for discovery
#         random_count = min(3, len(articles_data))
#         random_articles = random.sample(articles_data, random_count) if random_count > 0 else []
        
#         return render_template('index.html', 
#                              articles=latest_articles,
#                              popular_tags=popular_tags,
#                              random_articles=random_articles,
#                              total_articles=len(articles_data),
#                              total_tags=len(get_all_tags()),
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in home route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/article/<int:article_id>')
# def view_article(article_id):
#     """Article detail page with recommendations"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         # Find the article
#         found_article = None
#         for article in articles_data:
#             if article['id'] == article_id:
#                 found_article = article
#                 break
        
#         if found_article is None:
#             return render_template('404.html', 
#                                  message="Article not found", 
#                                  app_name=APP_NAME, 
#                                  version=VERSION), 404
        
#         # Increment view count
#         found_article['views'] = found_article.get('views', 0) + 1
        
#         # Get recommendations
#         recommendations = get_recommendations(article_id, limit=3)
        
#         return render_template('article.html', 
#                              article=found_article,
#                              recommendations=recommendations,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in article route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/search')
# def search():
#     """Search results page"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         query = request.args.get('q', '').strip()
#         tag = request.args.get('tag', '').strip()
        
#         results = []
#         search_type = ""
        
#         if tag:
#             results = search_articles(tag=tag)
#             search_type = f"Tag: #{tag}"
#         elif query:
#             results = search_articles(query=query)
#             search_type = f"Search: '{query}'"
#         else:
#             # If no search query, show all articles
#             results = articles_data
#             search_type = "All Articles"
        
#         # Get popular tags for sidebar
#         popular_tags = get_all_tags()[:12]
        
#         return render_template('search.html',
#                              results=results,
#                              search_type=search_type,
#                              total_results=len(results),
#                              popular_tags=popular_tags,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in search route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/tags')
# def tags_page():
#     """Browse all tags"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         all_tags = get_all_tags()
#         return render_template('tags.html', 
#                              tags=all_tags, 
#                              total_tags=len(all_tags),
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in tags route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/browse')
# def browse():
#     """Browse all articles with pagination"""
#     if not articles_data:
#         return render_template('error.html', 
#                              message="No articles found",
#                              app_name=APP_NAME, 
#                              version=VERSION)
    
#     try:
#         page = request.args.get('page', 1, type=int)
#         per_page = 6
        
#         total = len(articles_data)
#         start = (page - 1) * per_page
#         end = min(start + per_page, total)
#         articles = articles_data[start:end]
        
#         return render_template('browse.html',
#                              articles=articles,
#                              page=page,
#                              total=total,
#                              per_page=per_page,
#                              total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
#                              app_name=APP_NAME,
#                              version=VERSION)
#     except Exception as e:
#         print(f"Error in browse route: {e}")
#         return render_template('error.html', message=str(e), app_name=APP_NAME, version=VERSION)

# @app.route('/about')
# def about():
#     """About page"""
#     return render_template('about.html',
#                          app_name=APP_NAME,
#                          version=VERSION,
#                          total_articles=len(articles_data) if articles_data else 0,
#                          total_tags=len(get_all_tags()) if articles_data else 0)

# @app.route('/health')
# def health():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'app_name': APP_NAME,
#         'version': VERSION,
#         'timestamp': datetime.now().isoformat(),
#         'articles_loaded': len(articles_data) if articles_data else 0,
#         'total_tags': len(get_all_tags()) if articles_data else 0,
#         'total_views': sum(article['views'] for article in articles_data) if articles_data else 0
#     })

# # ============================================
# # API ENDPOINTS
# # ============================================

# @app.route('/api/articles')
# def api_articles():
#     """API endpoint to get all articles"""
#     return jsonify(articles_data)

# @app.route('/api/article/<int:article_id>')
# def api_article(article_id):
#     """API endpoint to get a single article"""
#     for article in articles_data:
#         if article['id'] == article_id:
#             return jsonify(article)
#     return jsonify({'error': 'Article not found'}), 404

# @app.route('/api/recommend/<int:article_id>')
# def api_recommend(article_id):
#     """API endpoint to get recommendations"""
#     recommendations = get_recommendations(article_id, limit=5)
#     return jsonify(recommendations)

# @app.route('/api/tags')
# def api_tags():
#     """API endpoint to get all tags"""
#     all_tags = get_all_tags()
#     return jsonify([{'tag': tag, 'count': count} for tag, count in all_tags])

# @app.route('/api/search')
# def api_search():
#     """API endpoint to search articles"""
#     query = request.args.get('q', '')
#     tag = request.args.get('tag', '')
    
#     if tag:
#         results = search_articles(tag=tag)
#     elif query:
#         results = search_articles(query=query)
#     else:
#         results = articles_data
    
#     return jsonify(results)

# # ============================================
# # ERROR HANDLERS
# # ============================================

# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html', 
#                          message="Page not found", 
#                          app_name=APP_NAME, 
#                          version=VERSION), 404

# @app.errorhandler(500)
# def internal_error(e):
#     return render_template('error.html', 
#                          message="Internal server error", 
#                          app_name=APP_NAME, 
#                          version=VERSION), 500

# # ============================================
# # MAIN ENTRY POINT
# # ============================================
# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("🚀 STARTING FLASK SERVER")
#     print("="*60)
#     print("📍 Open your browser and go to:")
#     print("📍 http://127.0.0.1:5000")
#     print("="*60 + "\n")
    
#     app.run(debug=True, host='127.0.0.1', port=5000)
