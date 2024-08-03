import random 
import aiohttp
import asyncio
import logging
import time
from bs4 import BeautifulSoup

class NewsGatherer:
    def __init__(self, search_queries, date_of_news, total_number_of_urls, output_file, location, language):
        self.search_queries = search_queries
        self.date_of_news = date_of_news
        self.total_number_of_urls = total_number_of_urls
        self.number_of_urls_per_query = total_number_of_urls // len(search_queries)
        self.output_file = output_file
        self.location = location
        self.language = language
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0"
        ]
        '''
        User agents are a list of different strings representing various web browsers and operating systems. These strings are used in the NewsGatherer class to mimic different user agents when making HTTP requests. User agents help websites identify the browser and operating system of the client making the request.
        '''

    async def fetch(self, session, url):
        headers = {'User-Agent': random.choice(self.user_agents)}
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logging.error(f"Request failed: {e}")
            return ""

    '''
    Google News might change its html layout in future. So we might need to change this function(extract_news_links) in future accordingly.To do this inspect the google news page and navigate to the news link. copy the class name and paste it here.
    '''
    def extract_news_links(self, soup):
        links = set()
        for a_tag in soup.find_all('a', href=True):
            if 'WwrzSb' in a_tag.get('class', []):  # Check if class contains 'WwrzSb'(change it in future if the code stops working)
                href = a_tag['href']
                if href.startswith('./read'):
                    full_url = "https://news.google.com" + href[1:]
                    links.add(full_url)
        return list(links)

    async def gather_news_links(self, search_query):
        if self.date_of_news.lower() == "anytime":
            url = f"https://news.google.com/search?q={search_query}&hl={self.language}&gl={self.location}&ceid={self.location}%3A{self.language}"
        else:
            search_query_with_date = f"{search_query} when:{self.date_of_news}"
            url = f"https://news.google.com/search?q={search_query_with_date}&hl={self.language}&gl={self.location}&ceid={self.location}%3A{self.language}"

        async with aiohttp.ClientSession() as session:
            response_text = await self.fetch(session, url)
            if not response_text:
                return []

            soup = BeautifulSoup(response_text, 'html.parser')
            links = self.extract_news_links(soup)  # Use the new method to extract links
            links = links[:self.number_of_urls_per_query]  # Limit links to desired number per query

            # Introduce a random delay to mimic human behavior and avoid rate-limiting
            await asyncio.sleep(random.uniform(1, 3))
            
            return links

    async def gather_and_save_news(self):
        all_links = set()
        for query in self.search_queries:
            links = await self.gather_news_links(query)
            all_links.update(links)
            if len(all_links) >= self.total_number_of_urls:
                break
        
        all_links = list(all_links)[:self.total_number_of_urls]  # Limit total links to desired number
        with open(self.output_file, "w") as file:
            for link in all_links:
                file.write(link + "\n")
        logging.info(f"News links saved to {self.output_file}")
# test run
if __name__ == "__main__":
    start = time.time()
    search_queries = ['Artificial intelligence']
    date_of_news = "1y"
    total_number_of_urls = 10
    location = "IN"
    language = "en"
    news_output_file = "links_test.txt"

    news_gatherer = NewsGatherer(search_queries, date_of_news, total_number_of_urls, news_output_file, location, language)
    asyncio.run(news_gatherer.gather_and_save_news())
    end = time.time()
    print(f"Time taken: {end - start} seconds")
