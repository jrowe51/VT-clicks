#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Varsity Tutors Instant Tutoring Bot


# In[1]:


#Once this file is on your local computer, you can insert your username and password below
username = "*******"
password = "*******"


# In[2]:


import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


import time
import json
import itertools

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException



# In[3]:


#Function to get the current number of opportunities
#1)Uses requests instead of selenium because this operation happens continuously 
#2)Have to get the token from the login page, but the session url is where you post the information
#3)Return of this function will be used to determine when new opportunities are available (num_opps increases) 

#Update 10.22.24 VT updated website and login page no longer requires authenticity token

def get_numopps() :


    LOGIN_URL = "https://www.varsitytutors.com/login/"
    session_url = "https://www.varsitytutors.com/session"

    
    # test = requests.get(LOGIN_URL, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}, proxies={"http": proxy}) 
    # htmlt = BeautifulSoup(test.text,"html.parser")
    # token2 = htmlt.find("input", {"name": "authenticity_token"})
    # key2 = token2.attrs["value"]
    # print(key2)
    
    
    
    with requests.session() as s: 
        req = s.get(LOGIN_URL, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'})#, proxies={"http": proxy})
        html = BeautifulSoup(req.text,"html.parser")
        #token = html.find("input", {"name": "authenticity_token"}).attrs["value"]
        #value = html.find("input", {"name": "utf8"}).attrs["value"]
    
    payload = { 
    	#"authenticity_token": token, 
    	"user[login]": username, 
    	"user[password]": password,
        #"utf8": value,
        #"user[remember_me]" : 1
    
    }
    
    res = s.post(session_url, data=payload, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'})#, proxies={"http": proxy}) 
    
    logged = s.get('https://www.varsitytutors.com/tutoring_opportunities', headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'})#, proxies={"http": proxy})
    #Webpage no longer coded in json, "logged" already in appropriate format
    #json_resp = logged.json()
    return logged
    
    
    #return req_dict['recordsTotal']


# In[4]:


#Function that determine if a web element is present before trying to click it
def check_exists_by_xpath(xpath, d):
    try:
        d.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


# In[ ]:


#Main body of code
#Updated 5.23.24
#1) Opens a chrome browser with some special options to avoid being flagged by the website
#2) Navigates to opportunity table and reads the initial amount of opportunities
#3) Constantly checks number of opporunities to see if new ones are added, clicks if so




#Remove automation flags
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

d= webdriver.Chrome(options = chrome_options)



d.get("https://www.varsitytutors.com/account/tutor")
d.find_element("name", "email").send_keys(username)
d.find_element("name", "password").send_keys(password)

d.find_element(By.XPATH, '//*[@id="root"]/div/main/div/div/form/button').click() 
time.sleep(10)

try :
    iframe = d.find_element(By.XPATH, '/html/body/div[3]/div[3]/div/iframe')
    d.switch_to.frame(iframe)    
    confirm_schedule = '//*[@id="root"]/div/div/div[1]/button'
    d.find_element(By.XPATH,confirm_schedule).click()
    d.switch_to.default_content()
except (NoSuchElementException ) as e :
    d.switch_to.default_content()



time.sleep(3)
d.find_element(By.XPATH, '//*[@id="tutor-account-app"]/nav/ul[1]/li[3]/a').click()
time.sleep(5)

try :
    iframe = d.find_element(By.XPATH, '//*[@id="vt-scheduling-ui-availability"]')
    d.switch_to.frame(iframe)    
    confirm_schedule = '//*[@id="root"]/div/div/div[1]/button'
    d.find_element(By.XPATH,confirm_schedule).click()
    d.switch_to.default_content()
except (NoSuchElementException ) as e :
    d.switch_to.default_content()




url = d.current_url



#Get page contents, find new opportunities table, num_rows is the total number of opportunities
soup = BeautifulSoup(d.page_source, 'html.parser')
opp_table = soup.find('table', class_='opportunity-table sortable dataTable no-footer')
num_rows = len(opp_table.tbody.find_all('tr'))




#THE LOOP 
#Compares number of rows to return from get_numopps, if it increases clicks the button, changes num_rows to return value
while True:

    #Logged is the website code in json. Have to decode to get total number of opportunities
    logged = get_numopps() 
    soup_df = pd.DataFrame(json.loads(logged.text))
    num_rows2 = soup_df['recordsTotal'][0]
    
    #Conditional for if table length changes
    if (num_rows2 > num_rows):
        
        #Loop to check each row of the table when the table has increased length
        for index, row in soup_df.iterrows():
            item = row['data']

            #Only operate on new opportunities that are instant
            if (item['status'] == 'New') :
                #Good_stuff dictionary has useful fields like 'instant', 'surge_rate', and 'occurences'
                good_stuff = item['desired_placement']
                opp_id = str(good_stuff['id'])
            
                #First Click routine to open the opportunity information
                if (good_stuff['instant']==True):
                    buttonname = '//*[@id="opportunity_' + opp_id + '"]/td[8]/a'
                    opp_button = WebDriverWait(d, 10, poll_frequency = 0.01).until(EC.presence_of_element_located((By.XPATH, buttonname)))
                                        print("You clicked on a new opportunity at " + now.time())

                    try :
                        opp_button.click()

                    except (NoSuchElementException,ElementNotInteractableException) as e:
                        break


                    #Have to wait 5 seconds before you can click again to accept on the opportunity. Please try to verify you can be helpful during these 5 seconds
                    time.sleep(5)
                    join_button = WebDriverWait(d, 50, poll_frequency = 0.1).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[6]/div/div/div[2]/div/div/div/div[1]/div/div[1]/div[3]/button')))

                    #SPAM clicking the button until you get the opportunity or it is no longer available
                    while True:
                        try :
                            # actionChains = ActionChains(d)
                            # actionChains.double_click(join_button).perform()
                            join_button.click()

                        except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                            break
                            
                    time.sleep(10)

                    
                    #If you don't get the opportunitiy, have to exit the information window
                
                    sorry = '/html/body/div[5]/div/div/div[2]/div/div/div/div[2]/div/button' 
                    cancel = '/html/body/div[6]/div/div/div[2]/div/div/div/div[2]/div/button'
                    if(check_exists_by_xpath(sorry, d)):
                        d.find_element(By.XPATH, sorry).click()
                    if(check_exists_by_xpath(cancel,d)):
                        d.find_element(By.XPATH, cancel).click()
                    if(check_exists_by_xpath('/html/body/div[6]/div/div/div[2]/div/div/div/div[1]/div/div[1]/div[3]/button', d)):
                        d.get('https://www.varsitytutors.com/tutoring_opportunities')
                    
                    else :
                        break
                
                    
        
        
        
    num_rows = num_rows2


# In[27]:


iframes = d.find_elements(By.TAG_NAME, "iframe")


# In[37]:


print(len(iframes))


# In[ ]:




