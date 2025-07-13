import os
import openai
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch
from dotenv import load_dotenv

#Load credentials
load_dotenv('.env')
#OpenAICompletionService
openai_completion_endpoint = os.getenv("OPENAI_COMPLETION_API_ENDPOINT")
openai_completion_key = os.getenv("OPENAI_COMPLETION_API_KEY")
openai_completion_model = os.getenv("OPENAI_COMPLETION_MODEL_NAME")
openai_completion_version = os.getenv("OPENAI_COMPLETION_API_VERSION")
#AzureSearchService
openai_search_source_endpoint = os.getenv("OPENAI_SEARCH_SOURCE_ENDPOINT")
openai_search_source_key = os.getenv("OPENAI_SEARCH_SOURCE_KEY")
openai_search_source_version = os.getenv("OPENAI_SEARCH_SOURCE_VERSION")

openai_search_endpoint = os.getenv("OPENAI_SEARCH_API_ENDPOINT")
openai_search_key = os.getenv("OPENAI_SEARCH_API_KEY")
openai_search_index = os.getenv("OPENAI_SEARCH_INDEX_NAME")
openai_search_model = os.getenv("OPENAI_SEARCH_MODEL_NAME")

app = FastAPI()


openai.api_base = openai_completion_endpoint
openai.api_key = openai_completion_key
openai.api_type = "azure"
openai.api_version = openai_completion_version


embeddings = OpenAIEmbeddings(
    deployment = openai_search_model,   # nombre exacto de tu deployment en Azure OpenAI
    model = openai_search_model,         # opcional, depende de cómo creaste tu deployment
    openai_api_type = "azure",
    openai_api_base = openai_search_source_endpoint,  # Ojo: NO es el de AI Search
    openai_api_key = openai_search_source_key,
    openai_api_version = openai_search_source_version         # o la versión que uses en Azure OpenAI
)
## Connect to Azure
acs = AzureSearch(azure_search_endpoint = openai_search_endpoint,
                  azure_search_key = openai_search_key,
                  index_name = openai_search_index,
                  embedding_function = embeddings.embed_query)

class Body(BaseModel):
    query:str

@app.get('/')
def root():
    return RedirectResponse(url = '/docs', status_code = 301)

@app.post('/ask')
def ask(body: Body):
    search_result = search(body.query)
    chat_bot_response = assistant(body.query, search_result)
    return {'response': chat_bot_response}

def search(query):
    docs = acs.similarity_search_with_relevance_scores(
        query=query,
        k=5,
    )
    results = docs[0][0].page_content
    print(results)
    return results

def assistant(query, search_results):
    messages=[
    {"role": "system", "content": "Asisstant is a chatbot that helps you find the best wine for your taste."},
    {"role": "user", "content": query},
    {"role": "assistant", "content": search_results}
    ]

    response = openai.ChatCompletion.create(
        engine=openai_completion_model,
        messages=messages,
    )

    return response['choices'][0]['message']['content']