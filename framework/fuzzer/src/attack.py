from imports import *
import env_fuzzer 
import input_elements
import json
import util
from collections import defaultdict


logger = logging.getLogger('fuzzer.attack')
class AttackServer():
  base_url = ""
  kernel_log = ""
  image_dir = ""

  vuln_list = []
  fw_db = {}


  #Identify which class of vulnerability is to be tested
  AttackServerMode = -1

  #Identify whether a page has been tested for CI or not
  Tested = -1

  #Check if we are operating it in the `no-map` mode
  Nomap = 0

  def __init__(self, webPage, url, kernel_file, image_dir, mode, fw_id):
    #Holds the directory where the unpacked filesystem is kept 
    self.image_dir = image_dir

    #Setting the base url which will be used for crafting other url
    self.base_url = url

    #Storing the path to the  kernel log for the firmware 
    self.kernel_log = kernel_file

    #Initialzing the mode in which the Attack module should function
    self.attack_server_mode = int(mode)

    #Payloads in-memory for the vulnerability being tested
    self.payloads = []
    
    #Firmware ID
    self.fw_id = fw_id 

    #Stores the log of FW under test
    self.fw_log = {}
    
    logger.debug( 'URL IS:%s' , url)
    #Reauthenticating just to be on the safe side
    util.util.check_and_rollback(webPage, url)
    webPage.get(url)
    #try:
    #  print('Current:', webpage.current_url)
    #  webPage.get(url)
    #except: 
    #  #pass
    #  logger.warning('Not able to access start url or exception raised by browser')

    if self.attack_server_mode == 1:
      logger.info('[CI] Command Injection Module activated')
    elif self.attack_server_mode == 2:
      logger.info('[XSS] XSS module activated')
    elif self.attack_server_mode == 3:
      logger.info('[BO] Overflow module activated')
    elif self.attack_server_mode == 4:
      logger.info('[NULL] Null Deref module activated')
    elif self.attack_server_mode == 5:
      logger.info('[COMB] Run all attack modules')
    elif self.attack_server_mode == 6:
      logger.error('[INFO] Information Disclosure Mode not yet implemented')
    else:
      logger.warning('Unknown attack server mode')
      exit()
    ###FORCED BROWSING MODULE
    #self.forced_browsing(webPage)
  
    

  #performing authentication using login credentials
  @staticmethod
  def perform_auth(webPage):
    try:
      text_elements = webPage.find_elements_by_xpath("//input[@type='text']")
      password = webPage.find_element_by_xpath("//input[@type='password']")
      try:
        submit = webPage.find_element_by_xpath("//input[@type='submit']")
      except:
        #found in Trendnet 0c*
        submit = webPage.find_element_by_xpath("//input[@type='button']")

      for element in text_elements: #finding login field
        if (element.is_displayed()):
          login = element #login field

      try:
        print (env_fuzzer.CREDENTIAL_FILE)
        with open(env_fuzzer.CREDENTIAL_FILE, 'r') as fp:
          cred = [line.rstrip() for line in fp]
          credentials = 'User:%s Pass:%s' % (cred[0], cred[1])
          logger.info('Credentials found, trying %s', credentials)
      except:
        logger.info("No default credential file found")

      if cred[0] == '#':
        login.clear()
      else:
        login.clear()
        login.send_keys(cred[0])

      if cred[1] != '#':
        password.clear()
        password.send_keys(cred[1])
      else:
        password.clear()
        pass
      
      submit.click()
      time.sleep(1)

    except:

      logger.debug('Default Auth failed..trying through URL')
      try:
        with open(env_fuzzer.CREDENTIAL_FILE, 'r') as fp:
          cred = [line.rstrip() for line in fp]
          credentials = 'User:%s Pass:%s' % (cred[0], cred[1])
          logger.info('Credentials found, trying %s', credentials)
      except:
        raise NotImplementedError("No default credential file found")

      auth_url = ('http://%s:%s@0.0.0.0:8080') % (cred[0], cred[1])
      webPage.get(auth_url)
        
  
  def forced_browsing(self,webPage):
    #finding all URL's not encountered during our spidering 
    undocumented_URL = list(set(AttackServer.vuln_list).difference(webURL.visited))
    with open(PROXY_MODE_FILE, 'w') as fp:
      fp.write('0')
    for url in undocumented_URL:
      logger.info('Undocumented URL:%s', url)
      webPage.get(url)

  
  '''
  Responsible for populating the payloads into memory
  based on the attack mode. 
  
  Parameters:
  attack_mode(int) - Specifies the attack mode of the 
  fuzzer

  Return:
  payload(list_int) - Returns the in-memory list of payloads
  '''
  def populate_payloads(self, attack_mode):

    payloads = []

    if attack_mode == 1:
      logger.info('[CI] Populating CI payloads')
      exploits_file = env_fuzzer.EXPLOIT_DB + '/ci.txt'
    elif attack_mode == 2:
      logger.info('[XSS] Populating XSS payloads')
      exploits_file = env_fuzzer.EXPLOIT_DB + '/xss.txt'
    elif attack_mode == 3:
      logger.info('[BO] Populating overflow payloads')
      exploits_file = env_fuzzer.EXPLOIT_DB + '/overflow.txt'
    elif attack_mode == 4:
      logger.info('[NULL] Populating Null deref payloads')
      exploits_file = env_fuzzer.EXPLOIT_DB + '/null_deref.txt'
    elif attack_mode == 5:
      logger.info('[ALL] Populating all payloads')
      exploits_file = env_fuzzer.EXPLOIT_DB + '/combine.txt'
    else:
      logger.warning("Attack Server mode not set...Exiting")
      exit(1)
      
    with open(exploits_file, 'r') as fp:
      for line in fp:
        line = line.strip('\n')
        #Ignoring commented lines
        if line[0] == '#':
          continue
        payloads.append(line)
  
    return payloads

  '''
  Retrieves the webpage to be tested, finds the interactive
  elements in the page and then deploys the attack
  
  Parameters:
  webPage(webdriver) - The headless web browser
  webpage_obj(list) - List with URL attribute objects
  payloads - The loaded payloads
  '''
  def deploy_attack(self, webPage, webpage_obj, url_obj, payloads):
    #TODO: Make sure the login page is checked
    url = url_obj.get_url(webPage)
    processed_url = []

    while url is not None:
      
      if util.util.url_processed(url, self.fw_id):
        url = url_obj.get_url(webPage)
        continue


      web_obj = webpage_obj[url]
      logger.info('[Fuzzer] Testing URL:%s', webPage.current_url)

      #Checking if the URL has frames and creating appropriate obj
      frame_list = webPage.find_elements_by_xpath("//iframe")
      if frame_list:
        web_obj.type = input_elements.Frames(frame_list) 
      else:
        web_obj.type = input_elements.NoFrames()

      #Find all interactive elements(buttons/radios/input fields"
      logger.info('[Fuzzer] FINDING ELEMENTS')
      web_obj.type.find_input_elements(webPage, web_obj.input_fields, web_obj.buttons)
      web_obj.type.print_attributes(web_obj.input_fields)
   
      logger.info('[Fuzzer] ATTACKING PAGE')
      self.attack_page(web_obj, webPage, payloads)
      # processed_url.append(url)

      url = url_obj.get_url(webPage)

      self.fw_log.update({'processed':processed_url})
      self.dump_results()
    

  def dump_results(self):
    '''
    Dumps all the results into the FW_DB
    '''
    AttackServer.fw_db[self.fw_id] = self.fw_log
    with open(env_fuzzer.LOG_FILE, 'w') as fp:
      json.dump(AttackServer.fw_db, fp)
  
  def dump_url(self, url_list):
    '''
    Dumps the crawled url into the database
    '''
    logger.info('Dumping URL list into DB FW_ID:%s', self.fw_id)
    self.fw_log.update({'URL_LIST':url_list})
    AttackServer.fw_db[self.fw_id] = self.fw_log
    with open(env_fuzzer.LOG_FILE, 'w') as fp:
      json.dump(AttackServer.fw_db, fp)
    
  def find_input(self,webPage,ide):
    input_cand = "//input[(@id = '%s') or (@name = '%s') or (@value = '%s')]" % (ide, ide, ide)
    #input_cand_1 = "//input[@name='%s']" % ide
    try:
      input_field = webPage.find_element_by_xpath(input_cand)
      return input_field
    except:
      raise ReferenceError("Element not found %s %s", ide, webPage.current_url)

  
  def attack_page(self, url, webPage, payloads):
    #Dictionaries which will hold the headers and the parameters for a request
    param = {}
    header = {}
    error_results = defaultdict(list)
    
    #Flag to detect whether a page has been tested via the fallback mechanism or not
    url.tested = 0

    #Switching proxy to `request trap` mode      
    util.util.switch_proxy_mode(env_fuzzer.CAPTURE)
    
    for button in url.buttons:
      logger.debug('[ATTACK] Test_Button:%s', url.type.get_attribute(button))
      util.util.check_and_rollback(webPage, url.name)

      #finding the request
      ret = url.type.find_request(button, header, param, url, webPage, self.kernel_log, self.fw_log)
      #logger.debug('Button:%s Tested:%d Return_val:%d', button[1], AttackServer.Tested, ret)
      if ret == env_fuzzer.REQUEST_FILE_NOT_GENERATED :
        logger.info('[ATTACK:DEPLOY_ATTACK] Request not generated for %s', url.name)
        error_results[url.name].append(button) 

      elif ret == env_fuzzer.POST:
        logger.info("\n[ATTACK:ATTACK_PAGE] POST request captured. URL:%s", header['magic_uri'])
        url.tested = 1
        header['magic_uri'] = AttackServer.base_url + header['magic_uri']
        self.deliver_payload('POST', param, header, webPage, payloads)
         
      elif ret == env_fuzzer.GET:
        logger.info("\n[ATTACK:ATTACK_PAGE] GET request captured. URL:%s", header['magic_uri'])
        url.tested = 1
        self.deliver_payload('POST', param, header, webPage, payloads)

      elif ret == env_fuzzer.UNHANDLED:
        logger.info("\n[ATTACK:ATTACK_PAGE] Unhandled Request")

    self.fw_log.update({'ERROR':error_results})

  def deliver_payload(self,method, param, header, webPage, payloads):

    if method == 'POST':
      url = ''
    else:
      url = 'http://0.0.0.0:8080'

    if len(payloads) == 0:
      logger.warning("[ATTACK:DELIVER_PAYLOAD] Empty payload set...exiting")
      exit(1)

    util.util.switch_proxy_mode(env_fuzzer.NOCAPTURE)

    if method == 'POST':
      
      print (header['magic_uri'])

      url += header['magic_uri']
      logger.info('[ATTACK:DELIVER_PAYLOAD] POST_URL:%s', url)
      
      try:
        del header['magic_uri']
      except KeyError:
        logger.warning('[ATTACK:DELIVER_PAYLOAD] URI not inferred')
       
      if self.attack_server_mode == 5:
        payload_count = 0
        for payload in payloads:
          logger.debug('Payload:%s count:%d', payload, payload_count)
          if payload_count == 0 :
            self.attack_server_mode = 4
            logger.debug("NPD activated")
          elif payload_count == 1:
            self.attack_server_mode = 3
            logger.debug("BO activated")
          elif payload_count >= 2 and payload_count < 69:
            self.attack_server_mode = 1
            logger.debug("CI activated")
          else:
            self.attack_server_mode = 2
            logger.debug("XSS activated")

          payload_count += 1
          
          if payload == '{}':
            payload = ''
          for key in param:
            param[key] = payload

          r = requests.post(url, data = param, headers = header)
          if self.detect_injection(r):
            #clearing the file so that future iterations don't 
            open(self.kernel_log, 'r+').truncate()
            self.log_payload(payload, url, param, header, method)
            break
          np.save(env_fuzzer.PARAMS, param)

      else:
        for payload in payloads:
          for key in param:
            param[key] = payload

          r = requests.post(url, data = param, headers = header)
          if self.detect_injection(r):
           #clearing the file so that future iterations don't 
            open(self.kernel_log, 'r+').truncate()
            self.log_payload(payload, url, param, header, method)
            break
          np.save(env_fuzzer.PARAMS, param)

    else:

      url += header['magic_uri']
      try:
        del header['magic_uri']
      except KeyError:
        logger.warning('URI not found')

      logger.debug("[ATTACK:DELIVER_PAYLOAD] GET_URL:%s", url)
      
      if self.attack_server_mode == 5:
        payload_count = 0
        for payload in AttackServer.Payloads:
          if payload_count == 0 :
            self.attack_server_mode = 4
            logger.debug("NPD activated")
          elif payload_count == 1:
            self.attack_server_mode = 3
            logger.debug("BO activated")
          elif payload_count >= 2 and payload_count < 69:
            self.attack_server_mode = 1
            logger.debug("CI activated")
          else:
            self.attack_server_mode = 2
            logger.debug("XSS activated")

          payload_count += 1

          if payload == '##':
            payload = ''
          logger.debug('Payload: %s',payload)
          for key in param:
            param[key] = payload

          #self.check_and_rollback(webPage, url)

          r = requests.get(url, headers = header, params = param) 
          if self.detect_injection(r):
            #clearing the file so that future iterations don't 
            open(self.kernel_log, 'r+').truncate()
            self.log_payload(payload, url, param, header, method)
            break
      else:
        for payload in payloads:
          for key in param:
            param[key] = payload

          r = requests.get(url, data = param, headers = header)
          if self.detect_injection(r):
            #clearing the file so that future iterations don't 
            open(self.kernel_log, 'r+').truncate()
            self.log_payload(payload, url, param, header, method)
            break
          np.save(env_fuzzer.PARAMS, param)

    #Switching proxy to `request-trap` mode again
    util.util.switch_proxy_mode(env_fuzzer.CAPTURE)

  def log_payload(self, payload, url, param, header, mode):
    if self.attack_server_mode == 1:
      logger.info('ATTACK VECTOR:%s PAYLOAD:%s URL:%s' , 'CI', payload, url)
    elif self.attack_server_mode == 2:
      logger.info('ATTACK VECTOR:%s PAYLOAD:%s URL:%s' , 'XSS', payload, url)
    elif self.attack_server_mode == 3:
      logger.info('ATTACK VECTOR:%s PAYLOAD:%s URL:%s' , 'BO', payload, url)

    
    #making a directory to store the exploit
    dir_name = hashlib.md5(url + mode).hexdigest() 
    path_dir = env_fuzzer.EXPLOITS + dir_name + '_' + mode
    logger.info('[Fuzzer] Exploit stored as %s', dir_name)
    if not os.path.exists(path_dir):
      os.makedirs(path_dir)

    #saving the param and headers
    np.save(path_dir + '/headers.npy', header)
    np.save(path_dir + '/param.npy', param)

    with open(path_dir + '/err.txt', 'w+') as fp:
      if self.attack_server_mode == 1:
        info = 'ATTACK VECTOR:%s PAYLOAD:%s URL:%s\n' % ('CI', payload, url)
      elif self.attack_server_mode == 2:
        info = 'ATTACK VECTOR:%s PAYLOAD:%s URL:%s\n' % ('XSS', payload, url)
      elif self.attack_server_mode == 3:
        info = 'ATTACK VECTOR:%s PAYLOAD:%s URL:%s\n' % ('BO', payload, url)
      elif self.attack_server_mode == 4:
        info = 'ATTACK VECTOR:%s PAYLOAD:%s URL:%s\n' % ('NULL', payload, url)
      fp.write(info)

    #copying the run script to recreate the exploit
    copy2(env_fuzzer.EXPLOIT_DB + '/poc.py', path_dir)

  def detect_injection(self, response):
    match_ci = re.compile(r"COMMAND INJECTION DETECTED");
    match_xss = re.compile(r"XSS");
    #regex to check if the stack trace printed
    match_ov = re.compile(r"\$[\s]*\d+[\s]*: [\d\w]+[\s][\d\w]+[\s][\d\w]+[\s][\d\w]+")

    if self.attack_server_mode == 1:
      logger.debug("[ATTACK:DETECT_INJECTION] Checking for CI")
      #Checking if the log has evidence of us opening the poison file
      for line in reversed(open(self.kernel_log, 'r').readlines()):
        if match_ci.search(line.rstrip()):
          return True
      return False 

    elif self.attack_server_mode == 2:
      logger.debug("[ATTACK:DETECT_INJECTION] Checking for XSS")
      #Checking if the poison string returned in response page
      if match_xss.search(response.text):
        return True
      else:
        return False

    elif self.attack_server_mode == 3 or self.attack_server_mode == 4:
      logger.debug("[ATTACK:DETECT_INJECTION] Checking for Null/BO")
      #Checking if stack trace printed in kernel log 
      for line in reversed(open(self.kernel_log, 'r').readlines()):
        if match_ov.search(line.rstrip()):
          return True
      return False
    else:
      logger.warning('[ATTACK:DETECT_INJECTION] Mode not set')
