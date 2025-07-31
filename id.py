import requests
from bs4 import BeautifulSoup

# インディータグのURL
url = "https://store.steampowered.com/tags/ja/インディー"

# リクエストを送信してHTMLを取得
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# タイトルを取得
games = soup.find_all('div', {'class': 'tab_item_name'})
for game in games:
    print(game.text)
