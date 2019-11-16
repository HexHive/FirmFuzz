#!/usr/bin/env python
from imports import *
from env_fuzzer import *
from attack import AttackServer
import mapper
from attribute_obj import attribute_obj

def main():
  find_auth_flag = 0 
  map_web_app = 0

  parser = argparse.ArgumentParser(description = 'Firmfuzz v1.0')

  parser.add_argument('-d', '--dir', required = True, \
      help = 'The location of the emulated firmware', metavar = 'FILE')

  parser.add_argument('-u', '--url' , \
      help = 'Use proxy at http://0.0.0.0:8080', \
      default = 'http://0.0.0.0:8080')

  parser.add_argument('--find_auth',  \
      help = 'Find authentication credentials', action = 'store_true') 

  parser.add_argument('--map_file', type = str, help = 'Provide file with pre-scraped URL')
  
  parser.add_argument('--scrape_fw', help = 'Scrape FW for URL', action='store_true') 

  parser.add_argument('-v', help='Toggle level of logging 1:Debug 2:Info', \
      default = '3')

  parser.add_argument('-a', '--attack', help='Attack Mode: 1:CI 2:XSS 3:BO 4:Null Deref 5:All', \
      required = True)

  args = parser.parse_args()
  url  = args.url
  
  #Setting the loglevel of the headless browser to only warnings
  LOGGER.setLevel(logging.WARNING)
  #Setting the warning for the requests package
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)


  firmware_kernel_log = args.dir + 'qemu.final.serial.log'
  firmware_workdir = args.dir + 'workdir/'
  firmware_id = args.dir.split('/')[-2]

  AttackServer.image_dir = args.dir 
  AttackServer.base_url = args.url

    
  with open('debug.log', 'w+' ) as fp:
    pass

  #setting the logging 
  logger = logging.getLogger('fuzzer')
  fh = logging.FileHandler('debug.log')
  fh_warn = logging.FileHandler('error.log')

  fh.setLevel(logging.DEBUG)
  fh_warn.setLevel(logging.WARNING)
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s', "%m-%d %H:%M")
  fh.setFormatter(formatter)
  fh_warn.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.addHandler(fh)
  logger.addHandler(ch)

  #setting the loglevel for firmfuzz
  if args.v == '1': 
    logger.setLevel(logging.DEBUG) 
  elif args.v == '2': 
    logger.setLevel(logging.INFO)
  else:
    pass

  util.util.switch_proxy_mode(env_fuzzer.NOCAPTURE)
#  #Initialising the headless browser  
  webPage = webdriver.Remote(desired_capabilities = webdriver.DesiredCapabilities.HTMLUNITWITHJS)
  try:
    webPage.get(url)
  except:
    logger.debug("[INFO] Error occurred while getting webpage")
    pass 
  

  #Performing authentication discovery if requested
  if args.find_auth:
    logger.info('[AUTH] Activating Authentication discovery module')
    ret = find_auth.find_auth(webPage)
    if ret == 1:
      logger.info('[AUTH] Discovery unsuccessful')
      exit(1)
    exit(0)

  try:
    with open(env_fuzzer.LOG_FILE, 'r') as fp:
      #Stores the entire database dict of fw details
      AttackServer.fw_db = json.load(fp)
      with open(env_fuzzer.BACKUP_LOG, 'a+') as fp:
        json.dump(AttackServer.fw_db, fp)
  except (IOError, ValueError):
    logger.info('No FW_DB present...initializing')
    pass

  AttackServer.perform_auth(webPage)
  frame_list = webPage.find_elements_by_xpath("//frame") 

  if frame_list:
    url_obj = mapper.ScrapeHrefWithFrames() 
  else:
    url_obj = mapper.ScrapeFlatHref()

  webpage_obj = {}
  
  if not args.map_file and not args.scrape_fw:
    try:
      url_obj.url_list = AttackServer.fw_db[firmware_id]['URL_LIST']
      logger.info('FW URL details found..skipping mapping')
    except KeyError:
      #Based on the scrape mode, find the URL 
        logger.info("FW URL details not present..scraping")
        url_obj.scrape_url(webPage)

  elif args.scrape_fw:
   logger.info("Scraping FW URL details")
   url_obj.scrape_url(webPage)
  
  elif args.map_file:
    logger.info('Mapped URL details found')
    with open(args.map_file, 'r') as fp:
      for line in fp.readlines():
        if line[0] == '#':
          continue
        url_obj.url_list.append(line.rstrip('\n'))
  

  #Creating attribute objects for each url
  for url in url_obj.url_list:
    print(url)
    webpage_obj[url] = attribute_obj(url)

  fuzzer_obj = AttackServer(webPage, url, firmware_kernel_log, firmware_workdir, args.attack, firmware_id)
  
  if not args.map_file and len(url_obj.url_list) != 0:
    fuzzer_obj.dump_url(url_obj.url_list)
    fuzzer_obj.dump_results()

  payloads = fuzzer_obj.populate_payloads(int(args.attack))

  fuzzer_obj.deploy_attack(webPage, webpage_obj, url_obj, payloads)

def check_state(webPage):

  print webPage.current_url
  if len(webPage.find_elements_by_xpath("//a")) > 1 and \
      len(webPage.find_elements_by_xpath("//input[@type='password']")) == 0:
    return 1
  else:
    return 0



if __name__ == '__main__':
  main()
