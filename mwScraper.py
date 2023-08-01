import urllib.request
import argparse
import datetime
import re
import pickle
import openai_keyword_generator as ai
import pandoc
from pandoc.types import *
from pathlib import Path
from bs4 import BeautifulSoup

class scraper:
    def __init__(self, url, output_path=None, posts_pickle=None, md_posts_pickle=None, api_key=None):
        if output_path:
            Path(output_path).mkdir(parents=True, exist_ok=True)
        self.output_path = output_path
        self.base_url = url
        self.post_list = self.get_post_list()
        if posts_pickle is None:
            self.wikitext_posts, self.failed_scrapes = self.scrape_posts()
            self.write_pickle(self.wikitext_posts, output_path + 'posts.pickle')
        else:
            self.wikitext_posts = self.load_pickle(posts_pickle)
        self.update_keywords(api_key=api_key)
        self.cleanup_ai_artifacts()
        if md_posts_pickle is None:
            self.markdown_posts = self.convert_posts_to_markdown()
            self.write_pickle(self.markdown_posts, output_path + 'md_posts.pickle')
        else:
            self.markdown_posts = self.load_pickle(md_posts_pickle)
        self.post_paths = self.output_posts()

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
        failed_scrapes = []
        scraped_posts = {}
        c = len(self.post_list)
        for i,post in enumerate(self.post_list, start=1):
            post_path = post['path']
            print('Scraping {} of {} - {}'.format(i,c,post_path))
            try:
                p = self.scrape_post(post_path)
                scraped_posts[p['title']] = p
            except:
                failed_scrapes.append(post)
                pass
        return scraped_posts, failed_scrapes

    # scrapes a post
    def scrape_post(self, post_path, name=None):
        url = self.base_url+post_path
        raw_url= url +'&action=raw'
        post_contents = self.scrape_url(raw_url)
        if name:
            title = name
        else:
            title = post_path.replace('?title=','').replace('_',' ')
        creation_time = self.get_creation_time(url)
        file_title = title.replace("%27",'').replace("%26",'')
        file_title = re.sub("[^0-9a-zA-Z]+", "-", file_title)
        file_name = f"{creation_time['creation_datetime'].strftime('%Y-%m-%d')}-{file_title}.md"
        return {'title': title, 'file_name': file_name, 'post_contents': post_contents, 'creation_time': creation_time['creation_time']}

    # gets creation time of a post provided the url
    def get_creation_time(self, url, tz=-500):
        request_url = f"{url}&action=info"
        post_raw_info = self.scrape_url(request_url)
        soup = BeautifulSoup(post_raw_info, features='html.parser')
        json_container = soup.find_all('tr', attrs={'id': 'mw-pageinfo-firsttime'})
        create_datetime_raw = json_container[0].text.replace('Date of page creation', '')
        create_datetime = datetime.datetime.strptime(create_datetime_raw,'%H:%M, %d %B %Y')
        create_datetime_str = datetime.datetime.strftime(create_datetime, "%Y-%m-%d %H:%M:%S {}".format(tz))
        return {'creation_time': create_datetime_str, 'creation_datetime': create_datetime}

    # gets the html contents of a url
    def scrape_url(self, url):
        session = urllib.request.urlopen(url)
        url_bytes = session.read()
        html_contents = url_bytes.decode("utf8")
        session.close()
        return html_contents

    def write_pickle(self, object, file_path):
        with open(file_path, 'wb') as pickle_file:
            pickle.dump(object, pickle_file)

    def load_pickle(self, file_path):
        with open(file_path, 'rb') as pickle_file:
            return pickle.load(pickle_file)

    def update_keywords(self, category_list=[], exclusion_list=[], api_key=None, update_pickle=True):
        c = len(list(self.wikitext_posts.keys()))
        for i,post in enumerate(list(self.wikitext_posts.keys()), start=1):
            if self.wikitext_posts[post].get('categories', None) is None:
                title = self.wikitext_posts[post]['title']
                print('Updating {} of {}: {}'.format(i,c,title))
                keyword_results = self.extract_keywords(post_contents=self.wikitext_posts[post]['post_contents'], title=self.wikitext_posts[post]['title'], category_list=category_list, exclusion_list=exclusion_list, api_key=api_key)
                self.wikitext_posts[post].update(keyword_results)

            if update_pickle:
                self.write_pickle(self.wikitext_posts, self.output_path + 'posts.pickle')

    # extract keywords and categories
    def extract_keywords(self, post_contents, title, category_list=[], exclusion_list=[], api_key=None):
        keywords = []
        categories = []
        if api_key:
            keyword_query = 'Generate a python list object format of food names and cooking method names found in the following recipe:\n{}'.format(title+'\n'+post_contents)
            keywords = ai.query(api_key=api_key, query=keyword_query)
            category_query = 'Generate a python list object format of food names and cooking method names found in the following recipe title. Do not include words that are not foods are cooking methods.:\n{}'.format(title)
            categories = ai.query(api_key=api_key, query=category_query)

        try:
            keywords = list(set(self.listToLower(eval(keywords))))
        except:
            pass

        try:
            categories = list(set(self.listToLower(eval(categories))))
        except:
            pass

        return {'keywords': keywords, 'categories': categories}

    def listToLower(self, input_list):
        return [x.lower() for x in input_list]

    def cleanup_ai_artifacts(self):
        c = len(list(self.wikitext_posts.keys()))
        for i, post in enumerate(list(self.wikitext_posts.keys()), start=1):
            try:
                keywords = self.wikitext_posts[post]['keywords']

                if 'food_names' in keywords:
                    food_names = keywords[keywords.find('food_names'):keywords.find(']')+1]
                    food_names = eval(food_names.replace('food_names = ',''))
                else:
                    food_names = []

                if 'cooking_methods' in keywords:
                    cooking_methods = keywords[keywords.find('cooking_methods'):keywords.find(']', keywords.find('cooking_methods')) + 1]
                    cooking_methods = eval(cooking_methods.replace('cooking_methods = ', ''))
                else:
                    cooking_methods = []

                if len(food_names) > 0 or len(cooking_methods)> 0:
                    self.wikitext_posts[post]['keywords'] = food_names + cooking_methods
            except:
                pass


    def convert_posts_to_markdown(self):
        markdown_posts = {}
        c = len(self.wikitext_posts)
        for i, post in enumerate(list(self.wikitext_posts.keys()), start=1):
            new_post = self.wikitext_posts[post]
            print('Converting {} of {} -- {}'.format(i, c, self.wikitext_posts[post]['title']))
            new_post['post_contents'] = self.generate_post_header(self.wikitext_posts[post]) + self.wikitext_to_markdown(
                self.wikitext_posts[post]['post_contents'])
            markdown_posts[new_post['title']] = new_post
        return markdown_posts

    def generate_post_header(self, post):
        header = '---\n'
        header += 'title: {}\n'.format(post.get('title', ''))
        header += 'date: {}\n'.format(post.get('creation_time', ''))
        header += 'categories: {}\n'.format(post.get('categories', ''))
        header += 'tags: {}\n'.format(post.get('keywords', ''))
        header += '---\n\n'
        return header

    def wikitext_to_markdown(self, wikitext):
        doc = pandoc.read(wikitext, format='mediawiki')
        markdown = pandoc.write(doc, format='markdown')
        return markdown

    def output_posts(self, style='markdown'):
        if style == 'markdown':
            posts = self.markdown_posts
        else:
            posts = self.wikitext_posts

        post_paths = []
        c = len(posts)
        for i,post in enumerate(list(posts.keys()), start=1):
            file_name = posts[post]['file_name']
            print('Outputing {} of {}: {}'.format(i,c,file_name))
            post_paths.append(self.output_file(posts[post]['post_contents'], file_name))

    def output_file(self, file_contents, file_name):
        filepath = f"{self.output_path}/{file_name}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_contents)
        return filepath

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', dest='url', default='https://danwiki.herokuapp.com/index.php')
    parser.add_argument('--output_path', dest='output_path', default='../output/mediawiki_export/')
    parser.add_argument('--posts_pickle', dest='posts_pickle', required=False) # ../output/mediawiki_export/posts.pickle
    parser.add_argument('--md_posts_pickle', dest='md_posts_pickle', required=False)  # ../output/mediawiki_export/md_posts.pickle
    parser.add_argument('--api_key', dest='api_key', required=False)

    args = parser.parse_args()
    s = scraper(url=args.url, output_path=args.output_path, posts_pickle=args.posts_pickle, md_posts_pickle=args.md_posts_pickle, api_key=args.api_key)


if __name__ == '__main__':
    main()