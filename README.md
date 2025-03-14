# Biotech News Bot

A FastHTML application that generates LinkedIn-ready summaries of recent biotech news from Endpoints News.

## Features

- Fetches recent articles from Endpoints News
- Generates AI-summarized content with category-appropriate emojis
- Formats as a LinkedIn-ready post with markdown formatting
- Copy to clipboard functionality

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```
2. Open your browser to http://localhost:5001
3. Click "Generate News" to fetch and summarize recent biotech news
4. Use the "Copy to Clipboard" button to copy the markdown-formatted text
5. Paste directly into LinkedIn or other platforms

## Configuration

You can modify the following variables in `app.py`:
- `DAYS_BACK`: Number of days to look back for articles (default is 7)
- The OpenAI model used (default is "gpt-4o")

## Requirements

- Python 3.7+
- OpenAI API key
- Internet connection to fetch RSS feeds 