# domain: self-explanatory
# pages: the url of the pages we want to to scrape (main page = "/"), written without the url_start "https://www."
# url_filter: a filter to find the actual article urls and not random urls to other sites etc
# url_exclusion: a filter to exclude unwanted urls on the site
# div_filter: a filter to find the actual text inside the article page
# p_attr_exclusion: a filter to exclude unwanted paragraphs in the article text, like for example promotional stuff, links/info about other articles etc
# pagin_filter: a filter to find the pagination links (HTML)

# the news sites for scraping
news_sites = [
{"domain": "huffpost.com", "pages": ["/", "/news", "/news/world-news"], "url_filter": r"/entry/", "url_exclusion": [], "div_filter": r"entry__content", "p_attr_exclusion": ["author-card", "slidedown"], "pagin_filter": "pagination__next-link"},
{"domain": "apnews.com", "pages": ["/", "/hub/us-news", "/hub/world-news"], "url_filter": r"/article/", "url_exclusion": [r"/article/photography-"r"/article/videos-"], "div_filter": r"Article|article-|Body", "p_attr_exclusion": ["social-caption"], "pagin_filter": ""},

{"domain": "edition.cnn.com", "pages": ["/world", "/world/africa", "/world/americas", "/world/asia", "/world/australia", "/world/china", "/world/europe", "/world/india", "/world/middle-east", "/world/united-kingdom"], "url_filter": r"^/\d+/\d+/\d+/", "url_exclusion": 
[r"/gallery/", r"/videos/"], "div_filter": r"article__content|pg-rail-tall__body|BasicArticle__main|pg-special-article__body", "p_attr_exclusion": [], "pagin_filter": ""},

{"domain": "news.com.au", "pages": ["/national", "/world"], "url_filter": r"news-story", "url_exclusion": [r"/video/"], "div_filter": r"story-primary", "p_attr_exclusion": [], "pagin_filter": ""},
{"domain": "aljazeera.com", "pages": ["/", "/middle-east"], "url_filter": r"/\d+/\d+/\d+/", "url_exclusion": [r"/gallery/", r"/liveblog/", r"/program/", r"/opinions/"], "div_filter": r"wysiwyg", "p_attr_exclusion": [], "pagin_filter": ""},
{"domain": "latimes.com", "pages": ["/", "/world-nation"], "url_filter": r"/story/", "url_exclusion": [], "div_filter": r"story", "p_attr_exclusion": ["promo"], "pagin_filter": "button load-more-button"},
{"domain": "vox.com", "pages": ["/", "/world-politics"], "url_filter": r"/\d+/\d+/\d+/", "url_exclusion": ["/videos/", "/podcasts/"], "div_filter": r"c-entry-content", "p_attr_exclusion": ["c-article", "amount", "contributed", "c-read-more"], "pagin_filter": "c-pagination"},
{"domain": "bbc.com", "pages": ["/news", "/news/world"], "url_filter": r"-\d+$", "url_exclusion": [r"/av/", r"/live/"], "div_filter": r"root", "p_attr_exclusion": ["PromoHeadline"], "pagin_filter": ""},
{"domain": "independent.co.uk", "pages": ["/", "/news/world"], "url_filter": r"-b\d+\.html", "url_exclusion": [r"/tv/"], "div_filter": r"main", "p_attr_exclusion": ["sc-qsla4c-4", "sc-5ejiri-5"], "pagin_filter": ""},
{"domain": "theguardian.com", "pages": ["/uk-news", "/world"], "url_filter": r"/\d+/[a-z]+/\d+/", "url_exclusion": [r"/live/", r"/gallery/", r"/video/"], "div_filter": r"maincontent", "p_attr_exclusion": ["ohmn7a", "1613jw2", "EmailSignup"], "pagin_filter": ""},
{"domain": "mg.co.za", "pages": ["/section/africa", "/section/world"], "url_filter": r"/world/\d+-\d+-\d+-", "url_exclusion": [r"in-brief-a-review"], "div_filter": r"entry-content", "p_attr_exclusion": [], "pagin_filter": ""},
{"domain": "usatoday.com", "pages": ["/", "/news/nation", "/news/world"], "url_filter": r"/story/", "url_exclusion": [r"/videos/"], "div_filter": r"truncationWrap", "p_attr_exclusion": [], "pagin_filter": ""},
{"domain": "buenosairesherald.com", "pages": ["/", "/world"], "url_filter": r"[.]com.{33}", "url_exclusion": [r"/wp-content/", r"/wp-json/", r"//fonts"], "div_filter": r"post-entry", "p_attr_exclusion": [], "pagin_filter": "next page-numbers"},

]

# Not free anymore. Started a paid subscription service:
# {"domain": "economist.com", "pages": ["/international"], "url_filter": r"/\d+/\d+/\d+/", "url_exclusion": [r"/interactive/"], "div_filter": r"css-13gy2f5", "p_attr_exclusion": [], "pagin_filter": "ds-pagination__nav-link"},

# "requests" header info minimizes the chance of being banned by the site, since we're simulating a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# initializing tables for the database
db_tables = [
        """CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            scrape_date DATETIME, 
            content TEXT);"""
    ,
        """CREATE TABLE IF NOT EXISTS exclude_articles (
            url TEXT PRIMARY KEY,
            reason TEXT);
        """
    ,
        """CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT);"""
    ,
        """CREATE TABLE IF NOT EXISTS keywords (
        keyword TEXT PRIMARY KEY,
        category_id INT,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE);"""
    ,
        """CREATE TABLE IF NOT EXISTS scrape_que (
        url TEXT PRIMARY KEY,
        scrape_time DATETIME,
        scrape_retries INT);"""
    ]

# initializing categories and keywords for the database
db_categories_keywords = {
    "business": ["economy", "market", "finance", "corporation", "stock", "investment", "startup", "entrepreneurship", "trade", "merger", "acquisition", "venture capital", 
    "taxation", "insurance", "real estate", "inflation", "investors", "investor", "interest rate", "sale", "bank", "profit", "debt", "central bank", "export", "import", 
    "supply chain", "business", "budget", "distribution", "logistics", "productivity", "unemployment", "net worth", "company", "companies", "loan", "money", "natural resources"],

    "technology": ["innovation", "digital", "smartphone", "computer", "artificial intelligence", "ai", "cybersecurity", "software", "internet", "hardware", 
    "big data", "cloud computing", "blockchain", "virtual reality", "augmented reality", "iot", "quantum computing", "robotics", "neural network", "natural language processing", 
    "autonomous", "software engineering", "3d printing", "digital transformation", "privacy", "tech", "technology", "technologies", "uav", "drone"],

    "sports": ["football", "basketball", "athletics", "olympics", "tennis", "golf", "baseball", "rugby", "cricket", "hockey", "volleyball", "boxing", "wrestling", "snooker", 
    "table tennis", "gymnastics", "swimming", "marathon", "triathlon", "racing", "snow sports", "championships", "motor sports", "ufc", "mma", "winter sports", "water sports", 
    "extreme sports", "skiing", "formula", "horse racing", "nfl", "nba", "epl", "premier league", "world cup", "world series", "soccer", "athlete", "athletes"],

    "entertainment": ["movies", "movie" "music", "television", "celebrities", "celebrity", "theater", "awards", "gaming", "books", "comics", "dance", "circus", "magic", "beauty",
    "stand-up comedy", "musical theater", "fashion",  "gossip", "media", "animation", "video games", "music festivals", "film festivals", "cinema", "hollywoord", "viral video", "opera",
    "podcast", "museum", "internet culture", "documentary", "exhibition", "art", "tv show", "tv series", "streaming", "entertainment", "actor", "actors", "actress", "actresses",
    "super bowl halftime"],

    "politics": ["government", "election", "policy", "diplomacy", "defense", "foreign affairs", "legislation", "regulation", "politics", "congress", "senate", 
    "house of representatives", "constitution", "justice system", "civil rights", "human rights", "national security", "immigration", "social justice", "corruption",
    "democracy", "political", "protests", "privacy laws", "nationalism", "foreign aid", "public opinion", "world leaders", "parliament", "president", "free speech", "court"],

    "health": ["medicine", "disease", "virus", "vaccine", "health care", "nutrition", "fitness", "wellness", "lifestyle", "pharmaceuticals", "hospital", "emergency services", "drug", 
    "mental health", "rehabilitation", "geriatrics", "pediatrics", "pathology", "oncology", "orthopedics", "depression", "therapy", "fertility", "population", "global population", 
    "aging population", "health issues", "pandemic", "epidemiology", "public health", "health risks", "addiction", "self-care", "cancer", "infection", "dementia", "life expectancy"],

    "environment": ["environment", "weather", "global warming", "sustainability", "renewable energy", "pollution", "climate change", "conservation", "ecology", "forestry", 
    "meteorology", "atmosphere", "solar energy", "wind energy", "extreme temperatures", "drought", "natural disaster", "wildfires", "fossil fuel", "sustainable energy",
    "gas emissions", "carbon emissions", "earthquake", "polar ice", "antarctic sea ice", "flooding", "cyclone", "clean energy", "wildlife conservation", "climate"],

    "science": ["research", "discovery", "astronomy", "astronomers", "biology", "chemistry", "physics", "mathematics", "engineering", "geology", "botany", "zoology", "oceanography", 
    "paleontology", "microbiology", "neuroscience", "genetics", "palaeontology", "quantum mechanics", "nanotechnology", "particle physics", "astrobiology", "astrophysics", "orbit",
    "universe", "galaxy", "galaxies", "light-years", "particle accelerator", "nuclear physics", "biochemistry", "evolutionary", "virology", "science", "nasa", "esa", "satellite"]
}