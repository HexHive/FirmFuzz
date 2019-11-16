import logging
import re
import numpy as np
import env_fuzzer
logger = logging.getLogger('fuzzer.parse')
class Parse:
  @staticmethod
  def parse_request(request_fp, header, param, url, kernel_log):
    lines = request_fp.readlines()
    head_line = lines[0].split(' ')

    if head_line[0] == 'POST':
      try:
        Parse.acquire_post(lines, header, param)
      except:
        logger.warning("Possibly the POST request format is unhandled, maybe multipart")
        return env_fuzzer.UNHANDLED_POST_REQUEST
    
      Parse.find_correlation(header, url, kernel_log)
      print (header['magic_uri'])
      
      #Storing the request headers for future use if needed
      np.save(env_fuzzer.HEADERS, header)
      return env_fuzzer.POST

    elif head_line[0] == 'GET':
      #Parse.acquire_get(lines, header, param)
      #np.save(env_fuzzer.HEADERS, header)
      #return env_fuzzer.GET
      return env_fuzzer.UNHANDLED

    else:
      return env_fuzzer.UNHANDLED

  @staticmethod
  def acquire_post(lines, header, param):
    header['magic_uri'] = lines[0].split(' ')[1]
    headers = lines[1:len(lines)-1]
    #Put all the headers into a (key,value) dict
    for line in headers:
      line = line.rstrip()
      temp = line.split(' ', 1)
      if temp[0] == 'Content-Length':
        continue
      header[temp[0]] = temp[1]
  
    #Put the message body params into a (key,value) dict
    param_temp = lines[-1].rstrip()
    list_file = param_temp.split("&")
    for word in list_file:
     temp = word.split('=', 1)
     param[temp[0]] = temp[1]
  
  @staticmethod 
  def acquire_get(lines, header, param):
    headers = lines[1:]
    #Put all the headers into a (key,value) dict
    for line in headers:
      line = line.rstrip()
      temp = line.split(' ', 1)
      if temp[0] == 'Content-Length' or len(line) == 0:
        continue
      header[temp[0]] = temp[1]
  
    #Put all the parameters into a (key,value) dict  
    request_line = lines[0].split(' ')
    request_line = request_line[1].rstrip()
    list_file = request_line.split('&')
    #for the first parameter in the GET request
    temp = list_file[0].split('?')
    list_file[0] = temp[1]
    header['magic_uri'] = temp[0]
    #list_file[0] = (re.findall(r'\?(.*)', list_file[0]))[0]
    
    for word in list_file:
      temp = word.split('=',1)
      try:
        param[temp[0]] = temp[1]
      except IndexError:
        logger.debug('IndexError during request parsing')
        param[temp[0]] = '' 

  #Finds all the resources which are touched on interacting with the URL
  @staticmethod
  def find_correlation(header, url, kernel_log): 

    executed_binary = []

    #Logging the top-level binary touched on URL interaction
    with open(env_fuzzer.CORRELATION_FILE, 'a+') as fp:
      top_level_bin = (header['magic_uri']).split('/')[-1]
      info = '%s\n%s\n' % (url, top_level_bin)
      fp.write(info)

    #Regex to capture all executed binaries
    match = re.compile(r"File::(.*)::")

    for line in reversed(open(kernel_log).readlines()):
      match1 = match.search(line.rstrip())

      if match1:
        
        binary = (match1.group(1)).split('/')[-1]
        if binary != top_level_bin:
          executed_binary.append((match1.group(1)).split('/')[-1])
        else:
          break
      else:
        continue

    #reversing to find the actual order of execution of binaries
    with open(env_fuzzer.CORRELATION_FILE, 'a+') as fp:
      for binary in executed_binary[::-1]:
        fp.write(binary + '\n')
