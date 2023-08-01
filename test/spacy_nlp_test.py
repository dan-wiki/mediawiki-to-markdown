import spacy  # Also run: python -m spacy download en_core_web_lg

category_list = ['poultry','chicken','beef','duck','lamb','fish','salmon','eggs','seafood','drinks','appetizers','dressings','shrimp','turkey']
exclusion_list = ['tsp','cup','tbsp','oz','ounce','pound','version','dp','drain','pan','season','skin','damage','halve','cavity','temp','hours','min','minutes','sec','seconds','half','time','total','optional','internal']

nlp = spacy.load("en_core_web_lg")
formatted_post_contents = re.sub("[^a-zA-Z]+", " ", title + post_contents)
doc = nlp(formatted_post_contents)
keywords = []
categories_basic = []
for token in doc:
    if token.is_stop:
        continue
    if token.pos_ == 'NOUN':
        if token.text not in exclusion_list and token.text in category_list:
            categories_basic.append(token.text)