import mitmproxy
from env_fuzzer import *

class ProxyLogger:

  def __init__(self,request_url):
    self.request_url = request_url

  def request(self,flow):
    with open(PROXY_MODE_FILE) as f:
      mode = f.readline()
    #Creating template request
    if mode == '1':
      print ('REQUEST CAPTURE MODE')
      headers = flow.request.headers
      request = flow.request.get_text(strict=True)
      string = ''
      if flow.request.method == 'GET' and \
          '?' not in flow.request.path:
        return
      string += flow.request.method + ' '
      string += flow.request.path + ' '
      string += flow.request.http_version + '\n'
      for k,v in headers.items():
        temp = '%s %s\n'%(k,v)
        string = string + temp
      with open(REQUEST_FILE, 'w+') as f:
        f.write(string)
        if len(request) > 0:
          f.write(request + "\n")

  def response(self,flow):
    with open(PROXY_MODE_FILE) as f:
      mode = f.readline()
    #Logging the response status code  
    if mode == '-1':
      self.normal_log_mode(flow)
    elif mode == '0':
      self.forced_browsing_mode(flow)

  def normal_log_mode(self,flow):
    status_code = str(flow.response.status_code)[0] #checking first digit of the error code
    if status_code == '4' or status_code == '5': #4xx or 5xx error code received
      fp1 = open(ERROR_FILE, 'a+')
      fp1.write(self.request_url + ' ' + str(flow.response.status_code) + '\n')
      fp1.close()
  
  def forced_browsing_mode(self,flow):
    status_code = str(flow.response.status_code)
    if status_code == '200':
      print('DISCLOSURE DETECTED')

def start():
  return ProxyLogger('placeholder') 
