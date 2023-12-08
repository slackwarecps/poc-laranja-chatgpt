# chatgpt.py
import requests
import uuid
import logging
import json
import os
from dotenv import load_dotenv, find_dotenv
import time

debug=False
load_dotenv(find_dotenv())

api_key = os.getenv("GPT_API_KEY")


# Endpoint da GPT-4 API
url_api = 'https://api.openai.com/v1'
assistant_id = 'asst_Z1pMBbuDlAQLLJ0nyTMttgHl'

# Cria um identificador único para a sessão da conversa
session_id = str(uuid.uuid4())

# Cabeçalhos para a requisição
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'OpenAI-Beta': 'assistants=v1',
}




def func_gpt_criar_thread():
  logging.info("name: "+ __name__)
  logging.info(' #4 Entrou na func_gpt_criar_thread')

  # Fazendo a requisição POST
  url = url_api + '/threads'
  response = requests.post(url, headers=headers)
  # Verifica se a requisição foi bem-sucedida
  if response.status_code == 200:
      # Extraindo a resposta
      response_data = response.json()
      # A resposta do chat pode ser encontrada em 'choices'
      #chat_response = response_data.get('choices', [{}])[0].get('text', '').strip()
      #print(response_data)
      logging.info(' #4 thread criada no chatgpt')
      return response_data
  else:
      logging.error(f"Erro ao fazer a requisição: {response.status_code}")
      return 'null'
  
  
  
def func_gpt_criar_mensagem(thread,mensagem):
  logging.info("name: "+ __name__)
  logging.info(' #5 Entrou na func_gpt_criar_mensagem ')  
  payload = {
            "role": "user",
            "content": mensagem
    }
  # Fazendo a requisição POST
  url = url_api + '/threads/'+thread+'/messages'
  response = requests.post(url, headers=headers,data=json.dumps(payload))
  #logging.info("status_code="+str(response.status_code))
  # Verifica se a requisição foi bem-sucedida
  if response.status_code == 200:
    logging.info("   #5 51 Mensagem criada com sucesso no chat gpt.")
    return response.json()
  else:
    logging.error("   #5 51 Falha ao criar mensagem no chat gpt.")
    logging.error(f"Status Code: {response.status_code}, Response: {response.text}")
    return 'null'

def func_gpt_rodar_assistente(thread):
  logging.info("name: "+ __name__)

  logging.info(' #9 Entrou na func_gpt_criar_mensagem ') 
  logging.info("ASSISTENTE_ID: asst_Z1pMBbuDlAQLLJ0nyTMttgHl")
  
  logging.info("thread: "+ thread)
  time.sleep(10)
  payload = {
         
                "assistant_id": 'asst_Z1pMBbuDlAQLLJ0nyTMttgHl'
    }
  # Fazendo a requisição POST
  url = url_api + '/threads/'+thread+'/runs'
  response = requests.post(url, headers=headers,data=json.dumps(payload))
  #logging.info("status_code="+str(response.status_code))
  # Verifica se a requisição foi bem-sucedida
  if response.status_code == 200:
    logging.info("   #9 Assistente foi acionado no chat gpt")
    logging.info(response.json())
    return response.json()
  else:
    logging.error("   #9 Falha ao Assistente foi acionado no chat gpt")
    logging.error(f"Status Code: {response.status_code}, Response: {response.text}")
    return 'null'
  
  
# RODA O ALGORITIMO DO CHATGPT RUN 
# 'expired','in_progress','completed'
def func_gpt_status_do_run_do_assistente(thread_id,run_id):
  logging.info(' #11 Entrou na func_gpt_status_do_run_do_assistente ') 
  logging.info("assistant_id: "+ assistant_id)
  logging.info("thread: "+ thread_id)
  # Fazendo a requisição POST
  url = url_api + '/threads/'+thread_id+'/runs/'+run_id
  response = requests.get(url, headers=headers)

  # Verifica se a requisição foi bem-sucedida
  if response.status_code == 200:
    logging.info("   #11 CHATGPT RUN")
    #logging.info(response.json())
    return response.json()
  else:
    logging.error("   #11 Falha ao CHATGPT RUN")
    logging.error(f"Status Code: {response.status_code}, Response: {response.text}")
    return 'null'



# Busca Mensagens da Thread 
def func_gpt_busca_mensagens(thread_id=''):
  logging.info(' #15 Entrou na func_gpt_busca_mensagens ') 
  logging.info("thread: "+ thread_id)
  # Fazendo a requisição POST
  url = url_api + '/threads/'+thread_id+'/messages'
  response = requests.get(url, headers=headers)

  # Verifica se a requisição foi bem-sucedida
  if response.status_code == 200:
    logging.info("   #15 busca_mensagens realizada com sucesso ")
    #logging.info(response.json())
    return response.json()
  else:
    logging.error("   #15 Falha ao busca_mensagens")
    logging.error(f"Status Code: {response.status_code}, Response: {response.text}")
    return 'null'