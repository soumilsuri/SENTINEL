from transformers import BartForConditionalGeneration, BartTokenizer
import re
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ArticleSummarizer:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
        self.model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

    @staticmethod
    def clean_text(text):
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
        return text.strip()

    def summarize_text(self, text):
        try:
            inputs = self.tokenizer.encode(text, return_tensors='pt', max_length=1024, truncation=True)
            summary_ids = self.model.generate(
                inputs, 
                max_length=150, 
                min_length=50, 
                length_penalty=2.0, 
                num_beams=4, 
                early_stopping=True,
                do_sample=True,
                top_k=50,
                top_p=0.95
            )
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary
        except Exception as e:
            logging.error(f"Error summarizing text: {e}")
            return "Error generating summary."

    def summarize_articles(self):
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            logging.error(f"Input file {self.input_file} not found.")
            return

        articles = content.split('Source ')
        summaries = []

        for article in articles:
            if not article.strip():
                continue

            parts = article.split('Text: ', 1)
            if len(parts) < 2:
                logging.warning(f"Article missing text body: {article[:50]}...")
                continue

            article_body = self.clean_text(parts[1])
            summary = self.summarize_text(article_body)
            summaries.append(summary)

        try:
            with open(self.output_file, 'w', encoding='utf-8') as file:
                for i, summary in enumerate(summaries, start=1):
                    file.write(f"Article {i} Summary:\n{summary}\n\n")
            logging.info(f"Summaries saved to {self.output_file}")
        except Exception as e:
            logging.error(f"Error writing summaries to file: {e}")

if __name__ == "__main__":
    start = time.time()
    input_file = "Content.txt"
    output_file = "summaries.txt"
    summarizer = ArticleSummarizer(input_file, output_file)
    summarizer.summarize_articles()
    logging.info(f"Summaries process completed.")
    end = time.time()
    print(f"Total time taken: {end - start:.2f} seconds")