import env_fuzzer
import requests
import logging
import subprocess
import time
from attack import AttackServer
logger = logging.getLogger('fuzzer.util')
'''
Module that provides a bunch of utility functions to help
the fuzzer maintain state and other things
'''
class util(AttackServer):
  '''
  Switches the proxy to either capture the traffic sent
  between the fuzzer and the emulated image or not

  Parameters: 
  mode(str): Signals what mode to put the proxy in
  '''

  @staticmethod
  def switch_proxy_mode(mode):
    with open(env_fuzzer.PROXY_MODE_FILE, 'w') as fp:
      fp.write(mode)

  '''
  Checks if the emulated firmware has reached an inconsistent state, 
  if so rollback to a consistent state
  '''
  @staticmethod
  def check_and_rollback(webPage, url):

    #Saving existing proxy mode
    with open(env_fuzzer.PROXY_MODE_FILE,'r') as fp:
      mode = fp.readline()
    
    if mode == '1':
      with open(env_fuzzer.PROXY_MODE_FILE, 'w') as fp:
        fp.write('0')
    else:
      pass
    
    r = requests.get(url)
    logger.info("[CHECK_AND_ROLL] Sending request to url:%s", url)
    logger.info("[CHECK_AND_ROLL] Code returned %d", r.status_code)

    if str(r.status_code)[0] == '5': 
      logger.info('[CHECK_AND_ROLL] Performing rollback of emulation')
      util.rollBack(webPage)
      webPage.get(url)
    else:
      pass
    
    #reverting the proxy to whatever mode
    with open(env_fuzzer.PROXY_MODE_FILE,'w') as fp:
      fp.write(mode)

  '''
  Function that performs the rollback
  '''
  @staticmethod
  def rollBack(webPage):

    logger.debug("[Util:rollback] Restarting emulation: %s", env_fuzzer.ROLLBACK_SCRIPT)
    rc = subprocess.call(env_fuzzer.ROLLBACK_SCRIPT,\
      shell= True)
    time.sleep(5) 
    webPage.get(AttackServer.base_url) 
    AttackServer.perform_auth(webPage)

  @staticmethod
  def url_processed(url, fw_id):
    try:
      if url in AttackServer.fw_db[fw_id]['processed']:
        return True
      else:
        return False
    except KeyError:
      logger.info('Processed table not generated')
      return False
