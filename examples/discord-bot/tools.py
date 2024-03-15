import requests
import os

def get_gif(keywords):
    giphy_api_key = os.environ["GIPHY_API_KEY"]
    """
    Searches for a GIF using the Tenor or Giphy API and returns the URL of the first result.

    Args:
        search_text (str): The search term to use.
        giphy_api_key (str): The Giphy API key.

    Returns:
        str: The URL of the first GIF result.
    """

    giphy_url = f"https://api.giphy.com/v1/gifs/search?q={keywords}&api_key={giphy_api_key}&limit=1"

    try:
        giphy_response = requests.get(giphy_url)
        giphy_json = giphy_response.json()
        giphy_gif_url = giphy_json["data"][0]["images"]["original"]["url"]
    except requests.exceptions.RequestException as e:
        print(e)
        giphy_gif_url = None

    if giphy_gif_url:
        return giphy_gif_url
    else:
        return None
