
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys, getopt
import os
import time
import getpass

driverPaths = {'Chrome': 'C:\Selenium\chromedriver.exe',
		'Edge': 'C:\Selenium\MicrosoftWebDriver.exe',
		'IE': 'C:\Selenium\IEDriverServer.exe'};
		
room = {'QA': 'https://rxpservices.hipchat.com/chat/room/4154443',
	'CCA': 'https://rxpservices.hipchat.com/chat/room/3554226',
	'TEST': 'https://rxpservices.hipchat.com/chat/room/4216688'
	};

url = 'https://www.hipchat.com/sign_in'
url2 = 'https://build.ccamatil.com/browse/OPD-OP11'
usr = 'thomas.rea@rxpservices.com'
usr2 = 'aureath'

lastBranchDeployed = "buildResult_OPD-OP11-41"

designatedRoom = room['TEST']

message = 'JUST A TEST - Deployment has been made on: '

def enterMessage(driver, xpath, message):
		element = driver.find_element_by_xpath(xpath)
		element.send_keys(message)
		time.sleep(0.1)
		element.send_keys(Keys.RETURN)

def reportToHipchat(driver, message):
	
	driver.get(url)
	
	xpath = '//*[@id="email"]'
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(usr)
	xpath = '//*[@id="signin"]'
	driver.find_element_by_xpath(xpath).click()
	
	xpath = '//*[@id="password"]'
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(passwd)
	xpath = '//*[@id="signin"]'
	driver.find_element_by_xpath(xpath).click()
	
	#proceed to web app
	xpath = '//*[@id="content"]/div/div/div/div[1]/div/a'
	driver.find_element_by_xpath(xpath).click()
	
	#wait for web app to load
	driver.implicitly_wait(10)#wait for outlet to load
	
	#select room
	driver.get(designatedRoom)
	
	#wait for web app to load
	#driver.implicitly_wait(30)#wait for outlet to load
	time.sleep(5)
	
	#enter message
	xpath = '//*[@id="hc-message-input"]'
	enterMessage(driver, xpath, message)
	
#Main Operation
#passwd2 = getpass.getpass('Jira password:')
passwd = getpass.getpass('Hipchat password:')

driver = webdriver.Chrome(driverPaths['Chrome'])

waitForDeployment = True #no way to end for now
while waitForDeployment:
	driver.get(url2) #list of branches

	xpath = '//*[@id="loginForm_os_username"]' #username field
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(usr2)
	
	xpath = '//*[@id="loginForm_os_password"]' #password field
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(passwd)
	
	xpath = '//*[@id="loginForm_save"]'
	driver.find_element_by_xpath(xpath).click()
	
	branchFound = False
	while not branchFound:
		xpath='//*[@id="buildResultsTable"]/tbody/tr[1]/td[1]/a'#first branch in list element containing id
		element = driver.find_element_by_xpath(xpath) #assumes there is at least one branch in list
		print('branch at top of list: ' + element.get_attribute('id'))
		if element.get_attribute('id') != lastBranchDeployed:
			lastBranchDeployed = element.get_attribute('id')
			xpath='//*[@id="buildResultsTable"]/tbody/tr[1]/td[1]'#element above to be clicked
			driver.find_element_by_xpath(xpath).click() # go to branch details
			branchFound = True
			print('found new branch: ' + lastBranchDeployed)
		else:
			print('no new branch...')
			sleep(10)
		
	found = False
	while not found:
		try: #find branch success/not successful tag
			element = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[2]/div/section[2]/div/div/div/div[1]/div[2]/div/div[2]/table/tbody/tr/td[2]/span'))
		)
		except:
			print('Cannot find success tag to even determine success or not')
			driver.quit()
		#see if tag says yes or not
		if element.text == 'SUCCESS':
			found = True
	#after success found then a message is posted to hipchat
	message = message + lastBranchDeployed
	reportToHipchat(driver, message)