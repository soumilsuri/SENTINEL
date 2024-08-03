import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging

class SeleniumLinkResolver:
    """
    Resolve final URLs of links that may have redirects using Selenium.
    Inputs:
    headless : bool, optional
        Whether to run the browser in headless mode (default is True).
    """
    def __init__(self, headless=True):
        self.headless = headless

    def initialize_driver(self):
        options = Options()
        if self.headless:
            options.headless = True
        options.add_argument('--disable-notifications')
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def get_final_url_selenium(self, driver, url):
        try:
            driver.get(url)
            time.sleep(2)
            return driver.current_url
        except Exception as e:
            logging.error(f"Error resolving URL {url}: {e}")
            return None

    def process_link(self, link, driver):
        link = link.strip()
        if link:
            final_url = self.get_final_url_selenium(driver, link)
            return link, final_url if final_url and final_url != link else None
        return link, None

    def process_links_in_batch(self, links):
        driver = self.initialize_driver()
        results = []
        for link in links:
            original_link, final_url = self.process_link(link, driver)
            results.append((original_link, final_url))
        driver.quit()
        return results

    def resolve_links(self, input_file, output_file, max_workers=5, batch_size=10):
        """
        Resolve the final URLs of links from an input file and save them to an output file.
        Inputs:
        input_file : str
            The file path to the input file containing the original links.
        output_file : str
            The file path to save the resolved final URLs.
        max_workers : int, optional
            The maximum number of threads to use for processing (default is 5).
        batch_size : int, optional
            The number of links to process in each batch (default is 10).
        """        
        with open(input_file, 'r') as file:
            links = [link.strip() for link in file.readlines()]

        resolved_links = [None] * len(links)
        batches = [(i, links[i:i + batch_size]) for i in range(0, len(links), batch_size)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_links_in_batch, batch[1]): batch[0] for batch in batches}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Resolving Links"):
                start_idx = futures[future]
                batch_results = future.result()
                for i, result in enumerate(batch_results):
                    original_link, final_url = result
                    resolved_links[start_idx + i] = final_url if final_url else original_link

        with open(output_file, 'w') as file:
            for resolved_link in resolved_links:
                file.write(resolved_link + '\n')

        logging.info(f"Resolved links have been written to {output_file}")

#test run
if __name__ == "__main__":
    start = time.time()
    selenium_resolver = SeleniumLinkResolver()
    selenium_resolver.resolve_links('links_test.txt', 'links.txt', max_workers=5, batch_size=10)
    ##change max_workers to change max number of chrome running
    end = time.time()
    print(f"Time taken: {end - start}")
