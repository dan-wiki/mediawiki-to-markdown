import openai

def query(api_key, query=None, temperature=.5, max_tokens=256, top_p=1, frequency_penalty=0, presence_penalty=0, get_models=False):
    openai.api_key = api_key
    if get_models:
        models = openai.Model.list()
        return models.data
    else:
        try:
            chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                           messages=[{"role": "user", "content": query}],
                                                           temperature=temperature,
                                                           max_tokens=max_tokens,
                                                           top_p=top_p,
                                                           frequency_penalty=frequency_penalty,
                                                           presence_penalty=presence_penalty)
            response = chat_completion.choices[0].message.content
            return response
        except:
            pass
            return ""
