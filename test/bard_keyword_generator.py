# key must be retrieved while incognito from
# Visit https://bard.google.com/
# F12 for console
# Session: Application → Cookies → Copy the value of __Secure-1PSID cookie.

from bardapi import Bard

def getKeywords(post_contents, bard_api_key_1, bard_api_key_2=None):
    token = bard_api_key_1
    bard = Bard(token=token)
    input_query = 'Generate list in python list object format of food and cooking methods from the following recipe. Please only include the python list object and nothing else in your response:\n{}'.format(post_contents)
    result = bard.get_answer(input_query)
    return result
