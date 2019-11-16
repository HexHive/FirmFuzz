from collections import defaultdict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
#from selenium import webdriver
import logging
from parse import Parse
import re
import env_fuzzer
import util
import os
logger = logging.getLogger('fuzzer.input_elements')
'''
This class dispatches the appropriate function
based on which object it was instantiated with
'''
class InputBaseClass():
  
  def find_input_elements(self, webPage, input_fields, buttons):
    raise NotImplementedError("Needs to be implemented by child class")
  
  def print_attributes(self, input_fields):
    raise NotImplementedError("Needs to be implemented by child class")
  
  def get_attribute(self, input_field):
    raise NotImplementedError("Needs to be implemented by child class")

  '''
  Finds an input element using the `id` or `value` atttribute

  Param:
  webPage(webDriver object): The headless web browser
  ide(string): HTML Input Identifier value
  
  Returns:
  input_field(webPage element): The corresponding webdriver element
  '''
  def find_input(self, webPage, ide):
    input_cand = "//input[(@id = '%s') or (@name = '%s') or (@value = '%s')]" % (ide, ide, ide)
    try:
      input_field = webPage.find_element_by_xpath(input_cand)
      return input_field
    except:
      raise ReferenceError("Element not found %s %s", ide, webPage.current_url)

  def parse_captured_request(self, header, param, url, webPage, kernel_log, button):  
    #finding the request parameter and headers
    try:
      with open(env_fuzzer.REQUEST_FILE, 'r') as fp:
        ret_value = Parse.parse_request(fp, header, param, url, kernel_log)
        os.remove(env_fuzzer.REQUEST_FILE) 
        util.util.check_and_rollback(webPage, url)
        return ret_value

    except IOError:
      logger.info('[IN_EL] PCR:Request file not generated %s\
          :%s' , url, button)
      return env_fuzzer.REQUEST_FILE_NOT_GENERATED

  def find_request(self):
    raise NotImplementedError("Needs to be implemented by child class")
   
'''
This class provides the frame-specific
functionality for: finding elements and 
finding requests
'''
class Frames(InputBaseClass):
  
  '''
  Puts all the names of the frame elements into a list

  Parameters:
  frame_elements(list webDriver) - Contains a list of all
  the `iframe` objects
  '''
  def __init__(self, frame_elements):
    self.frame_list = []
    if frame_elements:
      for frame in frame_elements:
        frame_name = frame.get_attribute("name")
        self.frame_list.append(frame_name)

  '''
  Finds all the interactive input elements on a webpage

  Parameters:
  webPage(webDriver) - The headless browser webpage
  '''
  def find_input_elements(self, webPage, input_fields, buttons): 

    for frame in self.frame_list:
      logger.debug("[FIND] Switch to frame %s", frame)
      webPage.switch_to_frame(frame)

      input_candidates = defaultdict(list)
      button_candidates = defaultdict(list)
        
      input_elements = webPage.find_elements_by_xpath("//input[(@type = 'text') or \
        (@type = 'password')]")
      if len(input_elements):
        input_candidates[frame].extend(input_elements)
      
      self.get_attribute(input_candidates, input_fields)

      button_elements = webPage.find_elements_by_xpath("//input[(@type = 'submit') or \
          (@type = 'SUBMIT') or (@type = 'button')]") 
      
      if len(button_elements):
        button_candidates[frame].extend(button_elements)
      self.get_attribute(button_candidates, buttons) 

      webPage.switch_to_default_content()

  '''
  Helper function to store the input attributes into a
  list with the corresponding frame name

  Parameters:
  input_candidates(dict) - Frame name as key and elements in frame
  as values

  input_list(list) - The list to contain the per frame
  input attributes passed as reference back to user
  '''
  def get_attributes(self, input_candidates, input_list):
    for key,value in input_candidates.iteritems():
      for element in value:
        if element.is_displayed() and element.is_enabled():
          if element.get_attribute("id") is not None:
            input_list.append([key, element.get_attribute("id")])
          elif element.get_attribute("name") is not None:
            input_list.append([key, element.get_attribute("name")])

          elif element.get_attribute("value") is not None:
            input_list.append([key, element.get_attribute("value")]);
          else:
            logger.warning("The required identification attributes(id,name,value) \
              do not exist")
  '''
  Finds a template request for the webpage passed to this function
  '''
  def find_request(self, button, header, param, url, webPage, kernel_log, fw_log):
    #Reading our database of discovered mac/ip HTML identifiers
    with open(env_fuzzer.IP_LIST, 'r') as fp:
      ip_list = fp.readlines()
    with open(env_fuzzer.MAC_LIST, 'r') as fp:
      mac_list = fp.readlines()

    missed_elements = defaultdict(list)

    #Regexes to match the input ID against  
    ip_regex = re.compile('lan|dhcp|ip')
    mac_regex = re.compile('mac')

    if button is None:
      logger.debug('[IN_EL:FIND_REQUEST] No buttons found')
      return env_fuzzer.NO_BUTTONS

    logger.debug('[IN_EL:FIND_REQUEST] Button: %s URL:%s' , button, url.name)

    for field in url.input_fields:
      logger.debug('[IN_EL:FIND_REQUEST] Switching to frame:%s', field[0])
      webPage.switch_to_frame(field[0])

      while True:
        logger.debug('[IN_EL:FIND_REQUEST] Finding field:%s',field[1])
        if ip_regex.search(field[1]) or field[1] in ip_list:
          payload = '192.168.10.1'

        elif mac_regex.search(field[1]) or field[1] in mac_list:
          payload = '8E:88:C4:54:EC:52'

        else:
          missed_elements[url.name].append(field[1]) 
          payload = 'dummy'
        
        #Checking if the input field already has some input in it
        try:
          input_field = self.find_input(webPage, field[1])
          if (input_field.get_attribute("value")) != '':
            break

          input_field.clear()
          input_field.send_keys(payload)
          logger.debug('[IN_EL:FIND_REQUEST] Field:%s Payload:%s' , field, payload)
          break
        except ReferenceError:
          logger.info('[IN_EL:FIND_REQUEST] Reference Error:%s' % field[1] )
          util.util.switch_proxy_mode(env_fuzzer.NOCAPTURE)

          util.util.check_and_rollback(webPage, url.name)
          webPage.get(url.name)
          webPage.switch_to_frame(field[0])
          
          util.util.switch_proxy_mode(env_fuzzer.CAPTURE)
          pass

      webPage.switch_to_default_content()
      
    webPage.switch_to_frame(button[0])
    try:
      self.find_input(webPage,button[1]).click()
    except:
      logger.error('Button %s not found, Frame:%s', button[1], button[0])
    try: 
      WebDriverWait(webPage, 0.001).until(EC.alert_is_present(), 'Timedoutwaitng')
      webPage.switch_to.alert.accept()
    except TimeoutException:
      pass
    webPage.switch_to_default_content()

    fw_log['MISSED_ELEMENTS'] = missed_elements

    return self.parse_captured_request(header, param, url.name, kernel_log, webPage, button[1])
  '''
  Print the attributes of the list

  Parameters:
  input_list(list) - Contains the list of attributes to be printed
  '''
  def print_attributes(self, input_list):
    logger.debug('Fields:%s' , (','.join(k[1] for k in input_list)))

  '''
  Prints the input attribute 

  Parameters:
  input_field(list): Input field `[frame, input_attribute]` 

  Returns:
  input_field[1](str): Attribute name
  '''
  def get_attribute(self, input_field):
    return input_field[1]

'''
This class provides the frame-specific
functionality for: finding elements and 
finding requests
'''
class NoFrames(InputBaseClass):
  
  '''
  Finds all the interactive input elements on a webpage

  Parameters:
  webPage(webDriver) - The headless browser webpage
  '''
  def find_input_elements(self, webPage, input_fields, buttons): 
    input_candidates = webPage.find_elements_by_xpath("//input[(@type = 'text') \
        or (@type = 'password')]") 
    self.get_attributes(input_candidates, input_fields)

    button_candidates = webPage.find_elements_by_xpath("//input[(@type = 'submit') or \
      (@type = 'SUBMIT') or (@type = 'button')]") 

    self.get_attributes(button_candidates, buttons)

  '''
  Helper function to store the input attributes into a
  list with the corresponding frame name

  Parameters:
  input_candidates(dict) - Frame name as key and elements in frame
  as values

  input_list(list) - The list to contain the per frame
  input attributes passed as reference back to user
  '''
  def get_attributes(self, input_candidates, input_list):
    for element in input_candidates:
      if (element.is_enabled()) and (element.is_displayed()):
        if element.get_attribute("id") is not None and len(element.get_attribute("id")) != 0:
            input_list.append(element.get_attribute("id"));
        elif element.get_attribute("name") is not None and len(element.get_attribute("name")) != 0:
            input_list.append(element.get_attribute("name"));
        elif element.get_attribute("value") is not None and len(element.get_attribute("value")) != 0:
            input_list.append(element.get_attribute("value"));
        elif element.get_attribute("onclick") is not None and len(element.get_attribute("onclick")) != 0:
            input_list.append(element.get_attribute("onclick"));
        else:
          logger.warning("The required identification attributes(id,name,value) \
              do not exist")

  '''
  Finds a template request for the webpage passed to this function
  '''
  def find_request(self, button, header, param, url, webPage, kernel_log, fw_log):
    #Reading our database of discovered mac/ip HTML identifiers
    with open(env_fuzzer.IP_LIST, 'r') as fp:
      ip_list = fp.readlines()
    with open(env_fuzzer.MAC_LIST, 'r') as fp:
      mac_list = fp.readlines()

    missed_elements = defaultdict(list)

    #Regexes to match the input ID against  
    ip_regex = re.compile('lan|dhcp|ip')
    mac_regex = re.compile('mac')

    if button is None:
      logger.debug('[IN_EL:FIND_REQUEST] No buttons found')
      return env_fuzzer.NO_BUTTONS

    logger.debug('[IN_EL:FIND_REQUEST] Button: %s URL:%s' , button, url.name)

    for field in url.input_fields:

      while True:
        logger.debug('[IN_EL:FIND_REQUEST] Finding field:%s',field)
        if ip_regex.search(field) or field in ip_list:
          payload = '192.168.10.1'

        elif mac_regex.search(field) or field in mac_list:
          payload = '8E:88:C4:54:EC:52'

        else:
          missed_elements[url.name].append(field)
          payload = 'dummy'
        
        #Checking if the input field already has some input in it
        try:
          input_field = self.find_input(webPage, field)
          if (input_field.get_attribute("value")) != '':
            break

          input_field.clear()
          input_field.send_keys(payload)
          logger.debug('[IN_EL:FIND_REQUEST] Field:%s Payload:%s' , field, payload)
          break
        except ReferenceError:
          logger.info('[IN_EL:FIND_REQUEST] Reference Error:%s' % field)
          util.util.switch_proxy_mode(env_fuzzer.NOCAPTURE)

          util.util.check_and_rollback(webPage, url.name)
          webPage.get(url.name)
          
          util.util.switch_proxy_mode(env_fuzzer.CAPTURE)
          pass

    try:
      self.find_input(webPage,button).click()
    except ReferenceError:
      logger.error('[IN_EL:FIND_REQUEST] Button %s not found', button)

    try: 
      WebDriverWait(webPage, 0.001).until(EC.alert_is_present(), 'Timedoutwaitng')
      webPage.switch_to.alert.accept()
    except TimeoutException:
      pass

    fw_log['MISSED_ELEMENTS'] = missed_elements

    return self.parse_captured_request(header, param, url.name, webPage, kernel_log, button)

  '''
  Prints the input attributes in the input_list
  
  Parameters:
  input_list(list): List of input elements or buttons
  '''
  def print_attributes(self, input_list):
    logger.debug('Fields:%s' , (','.join(k for k in input_list)))
  
  '''
  Prints the input attribute 

  Parameters:
  input_field(list): Input field `[frame, input_attribute]` 

  Returns:
  input_field[1](str): Attribute name
  '''
  def get_attribute(self, input_field):
    return input_field
