from flask import Flask, request

import chatgpt
from chatgpt import func_gpt_status_do_run_do_assistente
from chatgpt import func_gpt_busca_mensagens
from controllers.twiliox import func_responde_ao_cliente_pelo_whatsapp
import logging
from controllers.twiliox import func_twilio_chegou
import os
from dotenv import load_dotenv, find_dotenv
import time



load_dotenv('config/.env')



logging.basicConfig(filename='log/poc-laranja.log', encoding='utf-8', level=logging.INFO)
logging.debug('aplicacao iniciada')
logging.debug(' ')
logging.debug('****************************************')

api='/poc-laranja/v1/'

# Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
 
  logging.info('chegou na home page!')
  logging.info('AMBIENTE=' + os.getenv("AMBIENTE"))
  return 'POC Laranja v1.0', 200

@app.route('/teste', methods=['GET'])
def teste():

  logging.info('TESTE')
  print('T_THREAD=' + os.getenv("T_THREAD"))
  print('AMBIENTE=' + os.getenv("AMBIENTE"))
  func_gpt_busca_mensagens(os.getenv("T_THREAD"))
  return 'POC Laranja v1.0', 200



# twilio chamadas

@app.route(api+'comunicacao/chegou', methods=['POST'])
def chegou():
  logging.info('vai enviar a mensagem no whats')
  SmsMessageSid = request.form.get('SmsMessageSid')
  wa_id = request.form.get('WaId')
  logging.info('tel_origem='+wa_id)
  logging.info('SmsMessageSid='+SmsMessageSid)
  func_twilio_chegou(request)
  return 'OK mesmo 3', 201






@app.route(api+'comunicacao/health', methods=['GET'])
def health():
  return 'health', 200





# frontend chamadas

@app.route(api+'bff/conversa', methods=['GET'])
def funcao():
  chatgpt.funcao_01()
  return 'chamou a funcao 01', 200

@app.route(api+'bff/conversa/<int:id>/modo', methods=['POST'])
def funcao2(id):
  chatgpt.funcao_02()
  return str(id)+' modo da conversa alterado : Assistente desligado', 201

@app.route(api+'bff/parametro', methods=['POST'])
def funcao3():
  chatgpt.funcao_03()
  return 'parametro do sistema modificado ', 201


# Whatsapp Service twilio Callbacks
@app.route(api+'service/request', methods=['POST'])
def service_request():
  logging.info('POST >> no service_request')
  return '', 201

@app.route(api+'service/fallback', methods=['POST'])
def service_fallback():
  logging.info('POST >> no service_fallback')
  return '', 201

@app.route(api+'service/health', methods=['GET'])
def service_health():
  logging.info('GET >> no service_health')
  message_sid = request.values.get('MessageSid', None)
  message_status = request.values.get('MessageStatus', None)
  logging.info('SID: {}, Status: {}'.format(message_sid, message_status))

  return ('', 204)

####
### TESTES, sim depois pode apagar isso aqui :) #to-do
####
@app.route(api+'teste/envia-zap', methods=['POST'])
def teste_envia_zap():
  logging.info('POST >> no teste_envia_zap')
  logging.info('<<TO-DO ENVIAR PARA O WHATS AQUI>>>')  
  remetente='whatsapp:'+os.getenv("REMETENTE_TWILIO_WHATS") #jennifer numero
  mensagem='Com grandes poderes vem grandes responsabilidades, pequeno gafanhoto... #ale'
  destino='whatsapp:5511983477360' #Teste do Fabio
  func_responde_ao_cliente_pelo_whatsapp(remetente, mensagem,destino)
  return ('', 201)



if __name__ == "__main__":
  AMBIENTE = os.getenv("AMBIENTE")
  print('AMBIENTE='+AMBIENTE)
  BANCO = os.getenv("BANCO")
  print('BANCO='+BANCO)
  app.run(host="0.0.0.0", port=int("8080"), debug=False)
