import requests
from bs4 import BeautifulSoup

def get_href(body):
    soup = BeautifulSoup(body, 'html.parser')
    link = soup.find('a', href=True)
    return link['href']
  
url = 'https://source.unsplash.com/random/?hacker'
response = requests.get(url, allow_redirects=False)

print(get_href(response.content))
