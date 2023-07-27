import urllib.request
import argparse
import requests
import markdown
import datetime
from bs4 import BeautifulSoup

class scraper:
    def __init__(self, url):
        self.base_url = url
        self.raw_posts = self.scrape_url(self.base_url+'?title=Special:AllPages')
        self.post_list = self.get_post_list()

    def scrape_url(self, url):
        session = urllib.request.urlopen(url)
        url_bytes = session.read()
        html_contents = url_bytes.decode("utf8")
        session.close()
        return html_contents

    def get_post_list(self):
        soup = BeautifulSoup(self.raw_posts, features='html.parser')
        json_container = soup.find_all('ul', attrs={'class': 'mw-allpages-chunk'})
        posts = []
        for entry in json_container[0].select('a'):
            posts.append({'name': entry.attrs['title'], 'path': entry.attrs['href'].replace('/index.php','')})
        return posts

    def scrape_posts(self):
        scraped_posts = []
        for post in self.post_list:
            scraped_posts.append(self.scrape_post(post['path']))
        return scraped_posts

    def scrape_post(self, post_path):
        post_url= self.base_url+post_path+'&action=raw'
        post_contents = self.scrape_url(post_url)
        return post_contents

    def get_creation_time(url):
        """Get the creation time of a page from the MediaWiki API."""
        response = requests.get(f"{url}?action=info")
        info = response.json()
        return datetime.datetime.strptime(info["creation_time"], "%Y-%m-%dT%H:%M:%SZ")

    def generate_post_header(self, title, date, categories, tags):
        header = '---'
        header += 'title: {}'.format(title)
        header += 'date: {}'.format(date)
        header += 'categories: {}'.format(categories)
        header += 'tags: {}'.format(tags)
        header = '---'
        return header

    def convert_posts_to_markdown(self):
        print('placeholder')

    def convert_post_to_markdown(self, post_contents):
        print('placeholder')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://danwiki.herokuapp.com/index.php')
    parser.add_argument('--output_path', default='../output/mediawiki_export/')
    args = parser.parse_args()
    s = scraper(args.url)
    posts = s.scrape_posts()


if __name__ == '__main__':
    main()