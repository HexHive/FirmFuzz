'''
Responsible for creating a attribute object for each scraped URL
'''
class attribute_obj:

  def __init__(self, url):
    '''
    Instantiates the attributes for the URL
    Name(str) : URL
    input_fields(list): Holds the input fields which can have text entered
    buttons(list): buttons that trigger actions
    radios(list): radio buttons (not used yet for fuzzing)
    href_fields - ?
    type(obj): Holds whether URL is a Frame or Noframe object
    tested(int): Flag that signals whether the URL is tested or not
    '''
    self.name = url
    self.input_fields = []
    self.buttons = []
    self.radios = []
    self.href_fields = []
    self.type = None
    self.tested = 0

