# twilio.py
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
from services.parametro.service_parametro import func_parametros_busca_todos
#from services.socketio_cliente.py import func_socket_comando

import os
from dotenv import load_dotenv, find_dotenv
import requests
import json
import socketio
import globais


load_dotenv('config/.env')
VERSAO=os.getenv("VERSAO","V1")

def func_twilio_chegou(request):
  # Envia uma mensagem para o servidor
  #global sio
  #sio.emit('mensagem_criada', {'data':'twilio chegou'},broadcast=True)
  
  #globais.sio.emit('comando_criar_mensagem', {'data': 'chegou!!!'})
  
  #busca parametros
  beta1 = func_parametros_busca_todos()
  if 'Items' in beta1:
    beta=beta1['Items'][0]['numeros_beta_fabio']
  
  logging.info('================================ ')
  logging.info("name: "+ __name__)
  logging.info('Entrou na func_twilio_chegou')
  wa_id = request.form.get('WaId')
  mensagem=request.form.get('Body')
  ProfileName = request.form.get('ProfileName')
  logging.info('tel_origem='+wa_id)
  
  ## FASE 1 =================
  logging.info('TELEFONE= '+wa_id)
  logging.info('PERGUNTA= '+mensagem)
  logging.info('================================ ')
  logging.info(' ')
  logging.info(' ')
  logging.info(' ')
  ## CLIENTE JA ESTA CADASTRADO
  if verifica_cliente_esta_na_tabela(wa_id)==True:
    
    
    logging.info('  #1. cliente esta na base')    
    #verifica se esta usando o modo do Assistente
    cliente_modo = verifica_cliente_modo_assistente_ligado(wa_id)
    logging.info('  cliente_modo='+ str(cliente_modo))
    telefone=wa_id    

      
    
  ## CLIENTE NAO CADASTRADO PRIMEIRO ACESSO!!
  else:
    
    logging.info('  #1. cliente NAO esta na base, entao vai ser criado')
    resposta = dynamo_cliente_salvar(wa_id, ProfileName)
    logging.info("Cliente cadastrado com sucesso")
    #pprint(resposta, sort_dicts=False)
    telefone=wa_id
    cliente_modo = True
  
  ## FASE 2 ================= 

  # #2 Ja existe uma conversa ativa para esse numero/cliente?
  if VERSAO=='V1':
    existe_thread = verifica_existe_thread_cliente(telefone)
    print('existe thread = '+existe_thread)
    if existe_thread!='null':
      logging.info('  Sim Existe thread  :)')    
    else:
      logging.info('  Não existe thread  :(  )')      
      # 50 criar a thead do gpt
      thread_criada = func_gpt_criar_thread()
      print(thread_criada)
      existe_thread=thread_criada['id']
      # 4 Criar a thread no banco
      thread_db = dynamo_thread_salvar(telefone,thread_criada)
      logging.info(' #4 thread salva no banco de de dados :' + thread_criada['id'])


  if VERSAO=='V2':
    #existe_thread = verifica_existe_thread_cliente(telefone)
    #print('existe thread = '+existe_thread)
    #if existe_thread!='null':
    #  logging.info('  Sim Existe thread  :)')    
    #else:
    logging.info(' NAO VERIFICO THREAD LOGICA V2 CRIO SEMPRE UMA NOVA')      
    # 50 criar a thead do gpt
    thread_criada = func_gpt_criar_thread()
    print(thread_criada)
    existe_thread=thread_criada['id']
    # 4 Criar a thread no banco
    thread_db = dynamo_thread_salvar(telefone,thread_criada)
    logging.info(' #4 thread salva no banco de de dados :' + thread_criada['id'])

    
  # #5 Insere a Mensagem na thread

  if cliente_modo==True:
    thread=existe_thread
    retorno_msg=insere_mensagem_na_thread(telefone,thread,mensagem)
    
    # 9 Roda o Assistente
    dados_cliente=dynamo_cliente_busca_por_telefone(telefone)
    print(dados_cliente)
    beta_assistente_personalizado=''
    if 'assistant_id' in dados_cliente:
      beta_assistente_personalizado = dados_cliente['assistant_id']
      print(beta_assistente_personalizado)
    else:
      print('nao tem o assistant_id na tabela')
      
    run_id = roda_assistente(thread,telefone,beta_assistente_personalizado,beta)
    print('run_id='+run_id)
    print('thread='+thread)
    # 14 Aguarda JUMP para Fase Assincrona
    aguarda_execucao_do_assistente(thread,run_id,telefone)
  else:
    logging.info('  MODO_ASSISTENTE=FALSE!!! NAO VOU FAZER NADA!!!')



  
# ****************************
# FASE ASSINCRONA
# ****************************
def aguarda_execucao_do_assistente(thread,run_id,telefone_do_cliente):
  load_dotenv()
  logging.info(' #14 func_gpt_status_do_run_do_assistente')
  retorno = func_gpt_status_do_run_do_assistente(thread,run_id)
  logging.info(' status do run='+retorno['status'])
  
  contador_aguarde=0
  timeout_flag=False
  while contador_aguarde <= 300:
    logging.info('espera um pouco...'+ str(contador_aguarde))
    
    retorno = func_gpt_status_do_run_do_assistente(thread,run_id)
    #print('created_at='+str(retorno['created_at']))
    time.sleep(1)
    execucao_registro = retorno
    logging.info(' STATUS_THREAD='+retorno['status'])
    if (contador_aguarde ==180 ) or (retorno['status']=='completed'):
      ultimo_status=retorno['status']      
      if ultimo_status!='completed':
        logging.warning(' Saiu por time-out 120 segundos')
        timeout_flag=True
      
      break  
    contador_aguarde=contador_aguarde+1
  # 15 Se deu certo aguardar entao pega as mensagens do assistente e envia de volta.  
  if (timeout_flag==False):
    logging.info(' #15 deu certo... busca e filtra')
    logging.info(' ===================> VERSAO_LOGICA '+VERSAO)
    if VERSAO=='V2':
      logging.info(' LOGICA V2 ATIVA')
      dynamo_execucao_salvar(telefone_do_cliente,execucao_registro['id'],execucao_registro['thread_id'],str(execucao_registro['created_at']))
      # print('execucao id =')
      #logging.info( execucao_registro['id'])
      #time.sleep(10)


    logging.info(' #15 Vou aguarda 5 segundos para o chat-gpt conseguir responder todas as respostas.')
    time.sleep(5)
    # 15 busca as mensagens
    lista_de_mensagens_full =func_gpt_busca_mensagens(thread)
    # 16 filtra as mensagens
    #logging.info(' #16 Vou filtrar as mensagens')
    #lista_de_mensagens_assistente=filtra_as_mensagens_do_assistente(lista_de_mensagens_full)
    #print(lista_de_mensagens_assistente['data'])
    
    
    # 12 ENVIAR PARA O CLIENTE
    logging.info('ENVIA PARA O WHATS AQUI >>>')
    payload_json =lista_de_mensagens_full
    #print(payload_json)
  
    if 'data' in payload_json:
      data2 = payload_json['data']      
      for item in data2:
        if item['role'] == 'assistant':          
          linha =item['content'][0]['text']['value']          
          # 12 ENVIAR PARA O CLIENTE
          destino='whatsapp:'+telefone_do_cliente
          remetente='whatsapp:18647407407' # tem que ser o numero da Jennifer Assistente 
          mensagem=linha
          
          nome_cliente = dynamo_cliente_busca_por_telefone(telefone_do_cliente)
          #print(nome_cliente['nome'])
          time.sleep(2)
          func_responde_ao_cliente_pelo_whatsapp(remetente, mensagem,destino)
          data={'telefone':telefone_do_cliente,'nome':nome_cliente['nome'], 'conteudo':mensagem,'role':'assistant'}
          globais.sio.emit('comando_criar_mensagem',data)
  
  #logging.info(' www Apagando a thread desse cliente por enquanto')
  #if telefone_do_cliente not in ['5511983477360']:
    #thread_apagar(telefone_do_cliente)
  #time.sleep(10)
  logging.info(' :) FIM DO PROCESSO!!!')
  # limpar a thread
  
  logging.info('            ')
  logging.info('            ')
  logging.info(' ========================================== ')  
    
  return retorno, 200



  
def verifica_cliente_esta_na_tabela(telefone):  
  cliente = dynamo_cliente_busca_por_telefone(telefone)
  logging.info('  #6. busca cliente no banco :'+ telefone)
  if cliente!='null':
    print("Sim tem o telefone:")
    #pprint(cliente, sort_dicts=False)
    return True
  else:
    print('Nao tem o telefone '+telefone) 
    return False

def verifica_cliente_modo_assistente_ligado(telefone): 
  logging.info(' #8 Buscando Modo do Assistente do Cliente '+telefone) 
  cliente = dynamo_cliente_busca_por_telefone(telefone)  
  print(cliente['modo_assistente'])
  return cliente['modo_assistente']


def verifica_existe_thread_cliente(telefone):  
  thread = dynamo_thread_busca_por_telefone(telefone)
  logging.info('  #2. Verifica se existe thread para esse cliente')
  if thread!='null':
    logging.info("   #2 Sim existe uma thread ativa para esse telefone "+telefone)
    #pprint(thread, sort_dicts=False)
    return thread
  else:
    logging.info('   #2 Nao existe uma thread ativa '+telefone) 
    return 'null'
  
  

def insere_mensagem_na_thread(telefone,thread,mensagem):
  # 5 mensagem
  logging.info('  #5 Mensagem')
  mensagem_retorno=func_gpt_criar_mensagem(thread,mensagem)
  #print('mensagem')         
  #print(mensagem_retorno)
  dynamo_mensagem_salvar(telefone,mensagem_retorno,mensagem)
  nome_cliente = dynamo_cliente_busca_por_telefone(telefone)
  data={'telefone':telefone,'nome':nome_cliente['nome'], 'conteudo':mensagem,
        'role':'user'}
  globais.sio.emit('comando_criar_mensagem',data)




def dynamo_cliente_busca_por_telefone(telefone, dynamodb=None):
  logging.info('Buscando telefone '+ telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
    
  table = dynamodb.Table('cliente')
  try:
    response = table.get_item(Key={'telefone': telefone})
  except ClientError as e:
    print(e.response['Error']['Message'])
    logging.error('erro na busca!!!!!')
  else:
    if 'Item' in response: return response['Item']
    else:
      return 'null'
  
  
  
  
  
def dynamo_thread_busca_por_telefone(telefone, dynamodb=None):
  logging.info(' #2 Buscando thread ativa para o telefone '+ telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('thread')
  # Substitua pelo valor da chave de partição 'telefone' que você está buscando
  telefone_busca = telefone

  # Substitua pelo valor do campo 'status' que você quer filtrar
  status_filtar = 'ativo'
  
  try:    
    # A busca usando query com FilterExpression
    resposta = table.query(
       KeyConditionExpression=Key('telefone').eq(telefone_busca) & Key('status').eq(status_filtar)
    )    
    # Extrai e imprime os itens
    #items = resposta['Items']
    #for item in items:
    #  print(item['id'])    
    #print(resposta)   
    
  except ClientError as e:
    print(e.response['Error']['Message'])
    logging.error('erro na busca!!!!!')
  else:
    if 'Items' in resposta: 
        if resposta['Count']==0: 
          return 'null'  
        else:            
          return resposta['Items'][0]['id']
    else:
      return 'null'
  
  
  
  
  
def dynamo_cliente_salvar(telefone,ProfileName, dynamodb=None):
  logging.info(' #7. Insere Cliente na Base:' +telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')  
  # Para o fuso horário de Brasília use 'America/Sao_Paulo'
  timezone = pytz.timezone('America/Sao_Paulo')
  # Pega a data e hora atual no fuso horário de Brasília
  data_atual_br = datetime.now(timezone)
  epoch = data_atual_br.timestamp()  
  table = dynamodb.Table('cliente')
  ASSISTENTE_ID_VAR =  os.getenv("ASSISTENTE_ID_VAR")
  response = table.put_item( 
    Item={
        'telefone': telefone,
        'nome': ProfileName,
        'modo_assistente': True,
        'assistant_id':ASSISTENTE_ID_VAR,
        'created': str(epoch)
    }
  )
  return response

def dynamo_thread_salvar(telefone,thread_criada, dynamodb=None):
  logging.info(' #4 50. Insere Cliente na Base:' +telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')    

  table = dynamodb.Table('thread')
  lista=[]
  response = table.put_item( 
    Item={
        'telefone': telefone,
        'status': 'ativo',
        'id':thread_criada['id'],
        'created':thread_criada['created_at'],
        'messages':lista
        
    }
  )
  return response

def dynamo_mensagem_salvar(telefone,thread,mensagem, dynamodb=None):
  logging.info('   #5 51. Insere Mensagem na Base:' +telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb') 
  
  new_messages = [
    thread
  ]
  
  table = dynamodb.Table('thread')  
  response = table.update_item(
        TableName='thread',
        Key={
            'telefone':telefone,
            'status':'ativo'
        },
        
        UpdateExpression='SET #messages_list = list_append(#messages_list, :val1)',
        ExpressionAttributeNames={
            '#messages_list': 'messages'
        },
        ExpressionAttributeValues={':val1':new_messages},
        ReturnValues="UPDATED_NEW"
    )
  logging.info('    #5 51. Mensagem inserida na base')

  return response  





# Filtra as mensagens do assistente
def filtra_as_mensagens_do_assistente(lista_de_mensagens=[]):
  logging.info('    # =====>    Filtrando mensagens')
  retorno=lista_de_mensagens
  return retorno






def roda_assistente(thread,telefone='',beta_assistente_personalizado='',beta=[]): 
  logging.info(' #9 rodando o Assistente...')
  print('#9 beta')
  print(beta)
  run_id=func_gpt_rodar_assistente(thread,telefone,beta_assistente_personalizado,beta)
  return run_id['id']


# TWILIO :: ENVIO DE VOLTA PARA O CLIENTE
def func_responde_ao_cliente_pelo_whatsapp(remetente, mensagem,destino):  
  STATUS_CALLBACK = os.getenv("STATUS_CALLBACK")
  TWILIO_BASIC_RESPOSTA = os.getenv("TWILIO_BASIC_RESPOSTA")
  TWILIO_ACCOUNT_SID= os.getenv("TWILIO_ACCOUNT_SID")
  STATUS_CALLBACK=os.getenv("STATUS_CALLBACK")
  url = "https://api.twilio.com/2010-04-01/Accounts/"+TWILIO_ACCOUNT_SID+"/Messages.json"
  payload = 'To='+destino+'&From='+remetente+'&Body='+mensagem+'&StatusCallback='+str(STATUS_CALLBACK)
  headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Authorization': 'Basic '+TWILIO_BASIC_RESPOSTA
  }  
  response = requests.request("POST", url, headers=headers, data=payload)
  logging.info('    Resposta da twilio: ')
  logging.info('    >> : '+response.text)
  logging.info('    Enviou whatsapp pela twilio ')
  logging.info(     ' ')
  
  











#Apaga a thread  
def thread_apagar(telefone, dynamodb=None):
  logging.info(' #7. Insere Cliente na Base:' +telefone)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')  
  table = dynamodb.Table('thread')
  # Agora podemos deletar o antigo item
  response_deletar = table.delete_item(
      Key={
          'telefone': telefone,
          'status': 'ativo'
      }
  )
  logging.info('thread apagada:', response_deletar)
  return response_deletar

def dynamo_thread_todos(dynamodb=None):
  logging.info(' #2 Buscando thread Todos')
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('thread')

  response = table.scan()
  
  while 'LastEvaluatedKey' in response:
      response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
      for item in response['Items']:
          print(item['telefone'])
  return response


def dynamo_clientes_todos(dynamodb=None):
  logging.info(' #2 Buscando thread Todos')
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('cliente')

  response = table.scan()
  
  while 'LastEvaluatedKey' in response:
      response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
      for item in response['Items']:
          print(item['telefone'])
  return response


def dynamo_clientes_updatebyId(telefone,modo,dynamodb=None):
  logging.info(' #2 Atualizando o modo do assisten do cliente telefone='+telefone+' modo='+str(modo))
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('cliente')

  response = table.scan()
  
  # Atualiza o item na tabela
  response = table.update_item(
      Key={'telefone': telefone},
      UpdateExpression='SET modo_assistente = :val',
      ExpressionAttributeValues={':val': modo},
      ReturnValues="UPDATED_NEW"
  )
  logging.info(response)
  return response








def dynamo_parametro_todos(dynamodb=None):
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

def dynamo_execucao_todos(dynamodb=None):
  logging.info(' #2 Buscando dynamo_execucao_todos')
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('execucao')

  response = table.scan()
  
  while 'LastEvaluatedKey' in response:
      response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
      for item in response['Items']:
          print(item['telefone'])
  return response

def dynamo_execucao_salvar(telefone,run_id,thread_id,created_at, dynamodb=None):
  logging.info(' #4 50. Insere execucao na Base:' +telefone)
  logging.info(' #4 50. Insere execucao na Base:' +run_id)
  logging.info(' #4 50. Insere execucao na Base:' +thread_id)
  logging.info(' #4 50. Insere execucao na Base:' +created_at)
  if os.getenv("BANCO")=='LOCAL':
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
  else:
    dynamodb = boto3.resource('dynamodb')    

  table = dynamodb.Table('execucao')
  response = table.put_item( 
    Item={
        'telefone': telefone,
        'thread_id': thread_id,
        'run_id':run_id,
        'created_at':created_at        
    }
  )
  logging.info('>>>>>> Gravou a EXECUCAO NO BANCO')
  return response