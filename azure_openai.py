'''
app
azure_openai.py
'''
from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import HumanMessage



#with open('key.txt', 'r') as file:
#   key = file.readline().strip()

key= 'e6sk-proj-SquMmGT-EvQ_YJ5_q4vhXSeE_yH5MzPUPvNoexOc9c59TYE71q2kwk_sKabOiqoQDodfmiu7bTT3BlbkFJk9Wnpevjjd0Km_rCOKNGcgXB6iyScESh2rL4pZD0AhjS65POw0BdlLReeKU8H6mmvwWc3GlT8A'
llm35 = AzureOpenAI(
    deployment_name='ETHCI',
    openai_api_version='2023-05-15',
    openai_api_key=key,
    openai_api_base='https://lingpu.im.tku.edu.tw',
    openai_api_type='azure',
    model='gpt-35-turbo',
    temperature=0,
    max_tokens=80
)

chat35 = AzureChatOpenAI(
    deployment_name='ETHCI',
    openai_api_version='2023-05-15',
    openai_api_key=key,
    openai_api_base='https://lingpu.im.tku.edu.tw',
    openai_api_type='azure',
    model='gpt-35-turbo',
    temperature=1,
    max_tokens=2000
)

chat4 = AzureChatOpenAI(
    deployment_name='ETHCIGPT4',
    openai_api_version='2023-05-15',
    openai_api_key=key,
    openai_api_base='https://lingpu.im.tku.edu.tw',
    openai_api_type='azure',
    model='gpt-4',
    temperature=0.7,
    max_tokens=2000
)

embeddings = OpenAIEmbeddings(
    deployment='ETHCI-ada2',
    openai_api_key=key,
    openai_api_base='https://lingpu.im.tku.edu.tw',
    openai_api_type='azure',
    model='text-embedding-ada-002',
    chunk_size=1
)

msg = ''

#res = llm35(prompt=msg)
#print(f'\nllm35: {res}')

#res = chat35([HumanMessage(content=msg)])
#print(f'\nchat35: {res.content}')

#res = chat4([HumanMessage(content=msg)])
#print(f'\nchat4: {res.content}')

#e = embeddings.embed_query(msg)
#print(f'\nembed: len(e)={len(e)}')

'''

llm35:  (laughing)

I don't know, I don't know.

I don't know, I don't know.

I don't know, I don't know.

I don't know, I don't know.

I don't know, I don't know.

I don't know, I don't know.

I don't know, I don't know.

I don't know,

chat35: Why did the penguin sit on the fridge? Because he wanted to be cool!

chat4: Why did the penguin sit on the fridge?

Because he wanted to have a "cool" seat!

embed: len(e)=1536
'''