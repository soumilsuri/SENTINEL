import streamlit as st
import asyncio
import pandas as pd
from io import BytesIO
from googleNewsExtractor import NewsGatherer
from linkResolver import SeleniumLinkResolver
from linkScraper import WebScraper
from summarizer import ArticleSummarizer

# Page configuration
st.set_page_config(page_title="SENTINEL", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for blue theme and professional look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;700&display=swap');
    
    :root {
        --background-color: #0A192F;
        --text-color: #E6F1FF;
        --accent-color: #64FFDA;
        --secondary-color: #172A45;
    }

    body {
        font-family: 'Roboto', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .main-header {
        font-size: 40px;
        font-weight: bold;
        color: var(--accent-color);
        margin-bottom: 20px;
    }

    .sub-header {
        font-size: 22px;
        color: #8892B0;
        margin-bottom: 30px;
    }

    .stButton>button {
        color: var(--background-color);
        background-color: var(--accent-color);
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
    }

    .stButton>button:hover {
        background-color: #45E0BC;
    }

    .sidebar .sidebar-content {
        background-color: var(--secondary-color);
    }

    .sidebar .sidebar-content .stRadio > label {
        background-color: var(--secondary-color);
        color: var(--text-color);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }

    .sidebar .sidebar-content .stRadio > label:hover {
        background-color: #233554;
    }

    .stTextInput>div>div>input {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }

    .stSelectbox>div>div>select {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }

    .stTextArea textarea {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }
    </style>
    """, unsafe_allow_html=True)

# Main header
st.markdown('<p class="main-header">SENTINEL</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced News Analysis and Summarization</p>', unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.markdown("## Navigation")
    page = st.radio("", ["Dashboard", "Analysis Results"], key="navigation")

if page == "Dashboard":
    st.header("News Analysis Configuration")

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_queries = st.text_area("Search Queries (one per line)", height=100)
            num_urls = st.number_input("Number of URLs to analyze", min_value=1, max_value=100, value=10)
        
        with col2:
            location = st.selectbox("Location", ["IN", "US", "UK",  "CA", "AU"])
            language = st.selectbox("Language", ["en", "es", "fr", "de", "it"])
            date_of_news = st.select_slider("Date Range", options=["1d", "7d", "1m", "3m", "1y", "anytime"])

        submit_button = st.form_submit_button("Run Analysis")

    if submit_button:
        search_queries = search_queries.split('\n')
        if not search_queries:
            st.error("Please enter at least one search query.")
        else:
            with st.spinner("Analyzing news... This may take several minutes."):
                # Step 1: Google News Extraction
                news_output_file = "links_temp.txt"
                news_gatherer = NewsGatherer(search_queries, date_of_news, num_urls, news_output_file, location, language)
                asyncio.run(news_gatherer.gather_and_save_news())

                # Step 2: Link Resolution
                selenium_resolver = SeleniumLinkResolver()
                selenium_resolver.resolve_links('links_temp.txt', 'links.txt', max_workers=5, batch_size=10)

                # Step 3: Web Scraping
                scraper = WebScraper('links.txt')
                scraper.process_urls()

                # Step 4: Summarization
                summarizer = ArticleSummarizer("Content.txt", "summaries.txt")
                summarizer.summarize_articles()

            st.success("Analysis complete! View results in the 'Analysis Results' tab.")

elif page == "Analysis Results":
    st.header("News Analysis Results")

    try:
        # Read the summaries
        with open("summaries.txt", "r", encoding='utf-8') as f:
            summaries = f.read().split("\n\n")

        # Read the URLs and titles
        with open("heading.txt", "r", encoding='utf-8') as f:
            headings = f.read().split("\n\n")

        # Create a list to store the data
        data = []

        for summary, heading in zip(summaries, headings):
            heading_lines = heading.split("\n")
            if len(heading_lines) >= 2:
                url = heading_lines[0].replace("Link: ", "")
                title = heading_lines[1].replace("Heading: ", "")
                summary_text = summary.split("\n", 1)[1] if "\n" in summary else ""
                data.append({"Title": title, "URL": url, "Summary": summary_text})

        # Create a DataFrame
        df = pd.DataFrame(data)

        # Download button at the top
        if not df.empty:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            st.download_button(
                label="Download Analysis Results (Excel)",
                data=processed_data,
                file_name="sentinel_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Display the data
        for _, row in df.iterrows():
            st.markdown(f"### {row['Title']}")
            st.markdown(f"**Source:** [{row['URL']}]({row['URL']})")
            st.markdown(f"**Summary:** {row['Summary']}")
            st.markdown("---")

    except FileNotFoundError:
        st.info("No analysis results available. Please run an analysis from the Dashboard first.")
