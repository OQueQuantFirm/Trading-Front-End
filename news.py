# news.py
import os
from dotenv import load_dotenv
import requests

class CryptoNewsSentimentFetcher:
    def __init__(self):
        load_dotenv()  # Load variables from .env file
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://cryptocurrency-news2.p.rapidapi.com/v1/"

    def fetch_news_sentiment(self, source="coindesk"):
        """
        Fetch news sentiment related to cryptocurrency and bitcoin from the specified source.

        :param source: The news source (e.g., "coindesk").
        :return: News sentiment data in JSON format.
        """
        endpoint = f"{source}"
        url = f"{self.base_url}{endpoint}"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "cryptocurrency-news2.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            print(f"News API Response Status Code: {response.status_code}")
            print(f"News API Response Content: {response.content}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news sentiment: {e}")
            return None