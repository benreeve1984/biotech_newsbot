from fasthtml.common import *
import feedparser
import time
import os
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure OpenAI API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Time window: last 7 days
DAYS_BACK = 7

# JavaScript for clipboard functionality
clipboard_js = """
function copyMarkdown() {
  const content = document.getElementById('markdown-content');
  if (!content) return;
  
  // Legacy method
  if (document.queryCommandSupported && document.queryCommandSupported('copy')) {
    const textarea = document.createElement('textarea');
    textarea.textContent = content.textContent;
    textarea.style.position = 'fixed';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
      document.execCommand('copy');
      const btn = document.getElementById('copy-btn');
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy to Clipboard'; }, 2000);
    } catch (ex) {
      console.warn('Copy to clipboard failed.', ex);
      return false;
    } finally {
      document.body.removeChild(textarea);
    }
    return true;
  }
  
  // Modern method
  if (navigator.clipboard) {
    navigator.clipboard.writeText(content.textContent)
      .then(() => {
        const btn = document.getElementById('copy-btn');
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy to Clipboard'; }, 2000);
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
      });
  }
}
"""

# CSS styles inspired by Notion's clean aesthetic
styles = """
:root {
    --bg-color: #ffffff;
    --text-color: #37352f;
    --heading-color: #000000;
    --light-text: #6b7280;
    --border-color: #eaecef;
    --shadow-color: rgba(15, 15, 15, 0.05);
    --button-bg: #f7f6f3;
    --button-hover: #efeeeb;
    --button-active: #e9e8e4;
    --accent-color: #2e75cc;
    --code-bg: #f9f9f8;
}

@keyframes spinner {
    to {transform: rotate(360deg);}
}

.spinner-icon {
    display: inline-block;
    width: 16px;
    height: 16px;
    vertical-align: middle;
    border: 2px solid var(--light-text);
    border-right-color: transparent;
    border-radius: 50%;
    margin-right: 8px;
    animation: spinner 0.75s linear infinite;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, 'Apple Color Emoji', Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.5;
}

.biotech-news {
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
}

.headline {
    font-size: 1.1rem;
    margin-bottom: 1.5rem;
    color: var(--light-text);
    font-weight: 400;
}

.controls {
    margin: 30px 0;
    display: flex;
    align-items: center;
}

button {
    background-color: var(--button-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    color: var(--text-color);
    cursor: pointer;
    transition: background-color 0.2s;
}

button:hover {
    background-color: var(--button-hover);
}

button:active {
    background-color: var(--button-active);
}

#generate-btn {
    background-color: var(--accent-color);
    color: white;
    border: none;
}

#generate-btn:hover {
    opacity: 0.9;
}

#copy-btn {
    font-size: 14px;
}

.results {
    margin-top: 30px;
    padding: 20px 0;
    border-top: 1px solid var(--border-color);
}

#spinner {
    display: none;
    margin-left: 10px;
    color: var(--light-text);
    font-size: 14px;
    align-items: center;
}

#spinner.htmx-request {
    display: flex;
}

.copy-container {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
}

pre {
    background-color: var(--code-bg);
    padding: 20px;
    border-radius: 8px;
    white-space: pre-wrap;
    font-size: 15px;
    line-height: 1.6;
    box-shadow: 0 1px 2px var(--shadow-color);
    border: 1px solid var(--border-color);
    color: var(--text-color);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .biotech-news {
        margin: 20px auto;
    }
    
    pre {
        padding: 15px;
        font-size: 14px;
    }
}

.error {
    color: #e03e3e;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #ffd1d1;
    background-color: #fff5f5;
}

h1 {
    font-weight: 700;
    font-size: 2.2rem;
    color: var(--heading-color);
    margin-bottom: 2rem;
    padding-bottom: 0.5rem;
    letter-spacing: -0.03em;
}
"""

# Initialize app with headers for scripts and styles
app, rt = fast_app(
    # Set debug mode for development
    debug=True,
    # Define headers
    hdrs=(
        # Include clipboard functionality
        Script(clipboard_js),
        # Add custom styles
        Style(styles)
    )
)

def make_generate_button():
    """Create the generate button with HTMX attributes"""
    return Button(
        "Generate News", 
        id="generate-btn", 
        hx_post="/generate", 
        hx_target="#results",
        hx_indicator="#spinner"
    )

def make_copy_button():
    """Create the copy to clipboard button"""
    return Button(
        "Copy to Clipboard", 
        id="copy-btn", 
        onclick="copyMarkdown()"
    )

def make_loading_indicator():
    """Create the loading indicator"""
    return Div(
        Span(cls="spinner-icon"),
        "Generating news...",
        id="spinner", 
        cls="htmx-indicator"
    )

@rt("/")
def get():
    """Homepage route handler"""
    return Titled(
        "Biotech News Bot",
        Div(
            # Headline
            P("Generate LinkedIn-ready biotech news summaries from Endpoints News.", cls="headline"),
            # Controls section
            Div(
                make_generate_button(),
                make_loading_indicator(),
                cls="controls"
            ),
            # Results container
            Div(id="results", cls="results"),
            cls="biotech-news"
        )
    )

def fetch_rss_articles():
    """Fetch articles from Endpoints News RSS feed"""
    articles = []
    feed_url = "https://endpts.com/feed/"
    
    try:
        feed = feedparser.parse(feed_url)
        time_threshold = datetime.now() - timedelta(days=DAYS_BACK)
        
        for entry in feed.entries:
            # Parse published date (if available)
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            else:
                continue  # skip if no date available

            if published < time_threshold:
                continue

            articles.append({
                "title": entry.get("title", "No Title").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
                "published": published.strftime("%Y-%m-%d")
            })
    except Exception as e:
        print(f"Error fetching articles: {e}")
    
    return articles

def build_articles_text(articles):
    """Format articles for API prompt"""
    text_block = ""
    for art in articles:
        text_block += (
            f"Title: {art['title']}\n"
            f"Summary: {art['summary']}\n"
            f"URL: {art['link']}\n"
            f"Published: {art['published']}\n\n"
        )
    return text_block

def generate_summary(articles_text):
    """Generate summary using OpenAI API"""
    prompt = f"""
    You are an expert biotech news analyst. Given the following articles, generate a LinkedIn post summary with the most impactful 10 UK, Europe, and Middle-East articles as bullet points (no headings or footers, just the bullet points). For each bullet:
      - Start with an appropriate emoji from the following list based on the news category:
          - Regulatory & Approvals: 🏛️
          - M&A & Partnerships: 🤝
          - Clinical Trial Data: 🧪
          - Funding & IPO: 💰
          - Research & Innovation: 🔬
          - Press Releases & Announcements: 📢
          - Other high-impact biotech news: 🔍
      - Descriptive version of the article title (no link) without copying text verbatim.
    Group similar articles by category where appropriate.

    Articles:
    {articles_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4 for higher quality summarization
            messages=[
                {"role": "system", "content": "You are a helpful biotech news summarizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        summary = response.choices[0].message.content
        # Add the "Hopper's weekly biotech briefing" heading at the top
        summary = "# Hopper's weekly biotech briefing\n\n" + summary
        return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def create_results_container(summary):
    """Create the results container with summary and copy button"""
    return Div(
        Div(
            make_copy_button(),
            cls="copy-container"
        ),
        Pre(
            Code(summary, id="markdown-content")
        )
    )

@rt("/generate")
def post():
    """Handle news generation POST request"""
    articles = fetch_rss_articles()
    
    if not articles:
        return Div(
            P("No recent biotech articles found in the given timeframe."),
            cls="error"
        )
    
    articles_text = build_articles_text(articles)
    summary = generate_summary(articles_text)
    
    return create_results_container(summary)

# Run the server with auto-reload enabled
if __name__ == "__main__":
    serve(reload=True)
else:
    # For Vercel deployment - expose FastHTML app
    # This will be used by Vercel to create an API endpoint
    # without running the auto-reload server
    pass