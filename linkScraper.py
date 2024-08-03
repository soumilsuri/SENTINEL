import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class URLResolver:
    @staticmethod
    def resolve_url(url):
        try:
            response = requests.head(url, allow_redirects=True)
            return response.url
        except requests.RequestException:
            return url

class WebScraper:
    def __init__(self, file_path):
        self.file_path = file_path
        self.url_list = self.load_urls(file_path)
        self.driver = self.set_up_browser()
        self.url_resolver = URLResolver()
    
    @staticmethod
    def load_urls(file_path):
        url_list = []
        with open(file_path, 'r') as file:
            for line in file:
                url_list.append(line.strip())
        return url_list

    @staticmethod
    def set_up_browser():
        custom_headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            "Referer": "https://www.google.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            'User-Agent': "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36",
        }

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
        options.add_argument('custom_headers')
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def extract_data(self, link):
        logging.info(f"Extracting data from {link}")
        try:
            resolved_url = self.url_resolver.resolve_url(link)
            response = requests.get(resolved_url, allow_redirects=True)
            
            if response.status_code == 403:
                logging.warning(f"403 Forbidden error for {resolved_url}")
                return None, None, True  # Indicate that this URL should be removed
            
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')

            title = soup.find('title').text if soup.find('title') else 'No title found'
            paragraphs = [p.text for p in soup.find_all('p')]

            output = f'Title: {title}\n'
            for paragraph in paragraphs:
                output += f'Text: {paragraph}\n'
            output += '\n'
            return title, output, False  # False indicates that the URL should not be removed
        except Exception as e:
            logging.error(f"Error extracting data from {link}: {e}")
            return None, None, False

    @staticmethod
    def wait_if_required():
        if random.random() < 0.1:
            logging.info("Waiting for 10 seconds...")
            time.sleep(10)

    def process_urls(self):
        with open('Heading.txt', 'w', encoding='utf-8') as heading_file, open('Content.txt', 'w', encoding='utf-8') as content_file:
            i = 1
            urls_to_remove = []
            for url in self.url_list:
                if not url.startswith('http'):
                    logging.warning(f"Invalid URL: {url}")
                    continue
                try:
                    self.wait_if_required()
                    heading, data, should_remove = self.extract_data(url)
                    if should_remove:
                        urls_to_remove.append(url)
                    elif heading and data:
                        heading_file.write(f"Link: {url}\nHeading: {heading}\n\n")
                        content_file.write(f"Source {i}: {url}\n{data}\n")
                        i += 1
                except Exception as e:
                    logging.error(f"Error processing {url}: {e}")
            
            # Remove 403 Forbidden URLs from the list
            for url in urls_to_remove:
                self.url_list.remove(url)
            
            # Update the original file with the remaining URLs
            with open(self.file_path, 'w') as file:
                for url in self.url_list:
                    file.write(f"{url}\n")

#test run
if __name__ == "__main__":
    start = time.time()
    file_path = 'links.txt'
    scraper = WebScraper(file_path)
    scraper.process_urls()
    end = time.time()
    print(f"Total time taken: {end - start:.2f} seconds")
