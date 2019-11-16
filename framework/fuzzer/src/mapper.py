from selenium import webdriver
from collections import defaultdict
import logging
'''
This module is responsible for returning the different
url scraped from the router webpage.
'''
logger = logging.getLogger('fuzzer.map_url')
class Scrape(object):

  def __init__(self):
    self.url_list = []

  def scrape_url(self):
    raise NotImplementedError("Needs to be implemented by subclass")

  def get_url(self):
    raise NotImplementedError("Needs to be implemented by subclass")

  def scrape_href(self, webPage, url_list):
    '''
    Scrapes all the hrefs laid out in a flat profile on the root page

    Parameters:
    webPage (webPage.webdriver): The webdriver object
    url_list (list_str): List to contain the scraped URL
    '''
    blacklist = ['logout', 'javascript']
    attribute_elements = webPage.find_elements_by_xpath("//a");
    href_candidates = filter(lambda x: x.get_attribute("href"), attribute_elements)
    hrefs = map(lambda x: x.get_attribute("href"), href_candidates)
    for candidate in hrefs:
      if candidate not in url_list and candidate[-1] != '#' and not any(member in candidate for member in blacklist):
        try:
          webPage.get(candidate)
          url_list.add(candidate)
        except:
          logger.info('Skipping %s', candidate)
          continue
        self.scrape_href(webPage, url_list)
    return

  def remove_dead_links(self, url_list):
    '''
    Removes all duplicate URL and URL starting with #

    Parameters:
    url_list (list_str): List to contain the scraped URL

    Returns:
    url_list (list_str): The augmented scraped URL list
    '''
    url_list = filter(lambda x: "#" not in x, url_list)
    return set(url_list)

class ScrapeFlatHref(Scrape):
 
  def scrape_url(self, webPage):
    temp_list = set()
    self.scrape_href(webPage, temp_list)
    self.url_list = list(temp_list)

  def get_url(self, webPage):
    try:
      url = self.url_list.pop() 
      webPage.get(url)
      return url 
    except IndexError:
      return None

class ScrapeHrefWithFrames(Scrape):
 
  def scrape_url(self, webPage):
    #Checking if the URL has frames and creating appropriate obj
    frame_list = self.get_frames(webPage)
    current_url = webPage.current_url

    for frame in frame_list:
      temp_list = set()
      webPage.get(current_url)

      webPage.switch_to_frame(frame)
      self.scrape_href(webPage, temp_list) 

      self.url_list.extend(list(temp_list))
      webPage.switch_to_default_content()

  def get_frames(self, webPage):
    frame_list = []
    frame_elements = webPage.find_elements_by_xpath("//frame")
    for frame in frame_elements:
      frame_list.append(frame.get_attribute("name"))
    return frame_list

  def get_url(self, webPage):
    try:
      url = self.url_list.pop() 
      webPage.get(url)
      return url 
    except IndexError:
      return None
