# services/parametro
# service_parametro.py
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

from botocore.exceptions import ClientError
from pprint import pprint
from datetime import datetime
import pytz 
import time
from chatgpt import func_gpt_criar_thread
from chatgpt import func_gpt_criar_mensagem
from chatgpt import func_gpt_rodar_assistente
from chatgpt import func_gpt_status_do_run_do_assistente
from chatgpt import func_gpt_busca_mensagens

import os
from dotenv import load_dotenv, find_dotenv
import requests
import json


load_dotenv('config/.env')
VERSAO=os.getenv("VERSAO","V1")


def func_parametros_busca_todos(dynamodb=None):
  logging.info(' #2 dynamo_parametro_todos')
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('parametro')

  response = table.scan()
  
  while 'LastEvaluatedKey' in response:
      response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
      for item in response['Items']:
          print(item['telefone'])
  return response