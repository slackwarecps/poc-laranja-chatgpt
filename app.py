from flask import Flask, request

import chatgpt
import logging
from controllers.twilio import func_twilio_chegou
import os
from dotenv import load_dotenv

logging.basicConfig(filename='poc-laranja.log', encoding='utf-8', level=logging.INFO)
logging.debug('aplicacao iniciada')
logging.debug(' ')
logging.debug('****************************************')


api='/poc-laranja/v1/'




# Flask app
app = Flask(__name__)




@app.route('/', methods=['GET'])
def home():
  load_dotenv()
  logging.info('This message should go to the log file')
  print('AMBIENTE=' + os.getenv("AMBIENTE"))
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






if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int("8080"), debug=False)
