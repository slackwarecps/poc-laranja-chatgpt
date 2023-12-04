# twilio.py
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

from botocore.exceptions import ClientError
from pprint import pprint
from datetime import datetime
import pytz 
from chatgpt import func_gpt_criar_thread
from chatgpt import func_gpt_criar_mensagem
from chatgpt import func_gpt_rodar_assistente




def func_twilio_chegou(request):
  logging.info("name: "+ __name__)
  logging.info('Entrou na func_twilio_chegou')
  wa_id = request.form.get('WaId')
  mensagem=request.form.get('Body')
  ProfileName = request.form.get('ProfileName')
  logging.info('tel_origem='+wa_id)
  
  ## FASE 1 =================
  
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
  
  ## FASE 2 ================= 

  # #2 Ja existe uma conversa ativa para esse numero/cliente?
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
    
  # #5 Insere a Mensagem na thread

  #thread='thread_0ZCYJVCOLE_AQUI'
  thread=existe_thread
  retorno_msg=insere_mensagem_na_thread(telefone,thread,mensagem)
  
  #Roda o Assistente
  roda_assistente(thread)




def roda_assistente(thread): 
  logging.info(' #9 rodando o Assistente...')
  func_gpt_rodar_assistente(thread)
  
  




  
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




def dynamo_cliente_busca_por_telefone(telefone, dynamodb=None):
  logging.info('Buscando telefone '+ telefone)
  if not dynamodb:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
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
  if not dynamodb:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
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
  if not dynamodb:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")    
  # Para o fuso horário de Brasília use 'America/Sao_Paulo'
  timezone = pytz.timezone('America/Sao_Paulo')
  # Pega a data e hora atual no fuso horário de Brasília
  data_atual_br = datetime.now(timezone)
  epoch = data_atual_br.timestamp()  
  table = dynamodb.Table('cliente')
  response = table.put_item( 
    Item={
        'telefone': telefone,
        'nome': ProfileName,
        'modo_assistente': True,
        'created': str(epoch)
    }
  )
  return response

def dynamo_thread_salvar(telefone,thread_criada, dynamodb=None):
  logging.info(' #4 50. Insere Cliente na Base:' +telefone)
  if not dynamodb:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")    

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
  if not dynamodb:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")    
  
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

