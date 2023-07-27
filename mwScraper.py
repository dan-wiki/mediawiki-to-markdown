import urllib.request
import argparse
import requests
import datetime
import spacy
import re
from bs4 import BeautifulSoup

class scraper:
    def __init__(self, url, output_path=None):
        self.base_url = url
        self.post_list = self.get_post_list()
        self.wikitext_posts = self.scrape_posts()
        self.markdown_posts = self.convert_posts_to_markdown()
        self.post_paths = self.output_posts()

    # gets the html contents of a url
    def scrape_url(self, url):
        session = urllib.request.urlopen(url)
        url_bytes = session.read()
        html_contents = url_bytes.decode("utf8")
        session.close()
        return html_contents

    # gets the list of posts only
    def get_post_list(self):
        raw_posts = self.scrape_url(self.base_url + '?title=Special:AllPages')
        soup = BeautifulSoup(raw_posts, features='html.parser')
        json_container = soup.find_all('ul', attrs={'class': 'mw-allpages-chunk'})
        post_list = []
        for entry in json_container[0].select('a'):
            post_list.append({'name': entry.attrs['title'], 'path': entry.attrs['href'].replace('/index.php','')})
        return post_list

    # scrapes all posts
    def scrape_posts(self):
        scraped_posts = []
        c = len(self.post_list)
        for i,post in enumerate(self.post_list, start=1):
            post_path = post['path']
            print('Scraping {} of {} - {}'.format(i,c,post_path))
            scraped_posts.append(self.scrape_post(post_path))
        return scraped_posts

    # scrapes a post
    def scrape_post(self, post_path):
        url = self.base_url+post_path
        raw_url= url +'&action=raw'
        post_contents = self.scrape_url(raw_url)
        title = post_contents.replace('?title=','').replace('_',' ')
        creation_time = self.get_creation_time(url)
        keywords_cats = self.extract_keywords_cats(post_contents)
        file_name = f"{creation_time.strftime('%Y-%m-%d')}-{title}.md"
        return {'title': title, 'file_name': file_name, 'post_contents': post_contents, 'creation_time': creation_time,
                'keywords': keywords_cats['keywords'], 'categories': keywords_cats['categories']}

    def output_file(self, file_contents, file_name):
        filepath = f"{self.output_path}/{file_name}"
        with open(filepath, "w") as f:
            f.write(file_contents)
        return filepath

    def output_posts(self, style='markdown'):
        if style == 'markdown':
            posts = self.markdown_posts
        else:
            posts = self.wikitext_posts

        post_paths = []
        c = len(posts)
        for i,post in enumerate(posts, start=1):
            file_name = post['file_name']
            print('Outputing {} of {}: {}'.format(i,c,file_name))
            post_paths.append(self.output_file(post['file_contents'], file_name))


    # gets creation time of a post provided the url
    def get_creation_time(self, url):
        request_url = f"{url}&action=info"
        post_raw_info = self.scrape_url(request_url)
        soup = BeautifulSoup(post_raw_info, features='html.parser')
        json_container = soup.find_all('tr', attrs={'id': 'mw-pageinfo-firsttime'})
        create_datetime_raw = json_container[0].text.replace('Date of page creation', '')
        create_datetime = datetime.datetime.strptime(create_datetime_raw,'%H:%M, %d %B %Y')
        create_datetime_str = datetime.datetime.strftime(create_datetime, "%Y-%m-%dT%H:%M:%SZ")
        return create_datetime_str

    # extract keywords and categories
    def extract_keywords_cats(self, post_contents):
        nlp = spacy.load("en_core_web_lg")
        doc = nlp(post_contents)
        keywords = []
        categories = []
        for token in doc:
            if token.is_stop:
                continue
            if token.pos == spacy.PartOfSpeech.NOUN:
                keywords.append(token.text)
            elif token.pos == spacy.PartOfSpeech.ADJ:
                categories.append(token.text)
        return {'keywords': keywords, 'categories': categories}

    def generate_post_header(self, post):
        header = '---'
        header += 'title: {}'.format(post.get('title',''))
        header += 'date: {}'.format(post.get('date',''))
        header += 'categories: {}'.format(post.get('categories',''))
        header += 'tags: {}'.format(post.get('tags',''))
        header = '---\n\n'
        return header

    def convert_posts_to_markdown(self):
        markdown_posts = []
        for post in self.wikitext_posts:
            markdown_posts.append(self.generate_post_header(post) + self.wikitext_to_markdown(post['post_contents']))
        return markdown_posts

    def wikitext_to_markdown(self, wikitext):
      """Converts wikitext to markdown.

      Args:
        wikitext: The wikitext to convert.

      Returns:
        The markdown representation of the wikitext.
      """

      markdown = wikitext
      markdown = markdown.replace("'''", "**")
      markdown = markdown.replace("''", "*")
      markdown = markdown.replace("----", "---")
      markdown = markdown.replace("{{", "*[[")
      markdown = markdown.replace("}}", "]]")
      markdown = markdown.replace("[[", "[")
      markdown = markdown.replace("]]", "]")
      markdown = markdown.replace("* * *", "###")
      markdown = markdown.replace(";", ",")

      # Convert wikilinks to markdown links.

      markdown = re.sub(r"{{([^}]+)}}", r"*[[\1]]*", markdown)

      return markdown

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://danwiki.herokuapp.com/index.php')
    parser.add_argument('--output_path', default='../output/mediawiki_export/')
    args = parser.parse_args()
    s = scraper(args.url)
    posts = s.scrape_posts()


if __name__ == '__main__':
    main()