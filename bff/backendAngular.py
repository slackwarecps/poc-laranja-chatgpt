#backendAngular.py
import logging
import boto3
from flask import jsonify
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






