
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys, getopt
import os
import time
import getpass
import configparser
import re

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

class Environment:
	driverPaths ={}
	room = {}
	url = {}
	usr = {}
	lastBranchDeployed = ""
	config = ""
	designatedRooms = []
	mainRoom = ""
	message = ""
	login = False
	loginScriptLocation = ""
	loginArgs = ""
	passwd = ""
	
	def __init__(self, passwd):
		self.driverPaths = {'Chrome': 'C:\Selenium\chromedriver.exe',
				'Edge': 'C:\Selenium\MicrosoftWebDriver.exe',
				'IE': 'C:\Selenium\IEDriverServer.exe'
				};
		
		self.room = {'TEST-NOTIF': 'https://rxpservices.hipchat.com/chat/room/4292319',
				'CCA': 'https://rxpservices.hipchat.com/chat/room/3554226',
				'TEST': 'https://rxpservices.hipchat.com/chat/room/4216688',
				'DEFAULT': 'https://rxpservices.hipchat.com/chat/room/4216688',
				'NONE': ''
				};
		
		self.url['hipchat'] = 'https://www.hipchat.com/sign_in'
		self.url['branch'] = 'https://build.ccamatil.com/browse/OPD-OP12'
		self.usr['hipchat'] = 'thomas.rea@rxpservices.com'
		self.usr['jira'] = 'aureath'
		
		f = open('data','r') #read 
		self.lastBranchDeployed = f.read()
		
		config = configparser.ConfigParser()
		config.read('config.ini')
		
		self.url['project'] = config['DEFAULT']['project']
		#parts:
		#config - string
		#room - dictionary of room names to url
		#designatedRooms holds all the urls of rooms
		roomNames = config['DEFAULT']['designatedRooms'].strip().replace(" ","").split(",")
		for roomName in roomNames:
			self.designatedRooms.append(self.room[roomName])
		mainRoom = self.room[config['DEFAULT']['mainRoom']]
		self.message = config['DEFAULT']['message']
		self.login = str2bool(config['LOGIN']['login'])
		self.loginScriptLocation = config['LOGIN']['loginScriptLocation']
		self.loginArgs = config['LOGIN']['loginArgs']
		print('python CCA_autologin.py ' + self.loginArgs)
		print('can login? ' + str(self.login))
		
		self.passwd = passwd

def login (driver, usr, passwd):
	xpath = '//*[@id="loginForm_os_username"]' #username field
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(usr)
	
	xpath = '//*[@id="loginForm_os_password"]' #password field
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(passwd)
	
	xpath = '//*[@id="loginForm_save"]'
	driver.find_element_by_xpath(xpath).click()

def enterMessage(driver, xpath, message):
	element = driver.find_element_by_xpath(xpath)
	element.send_keys(message)
	time.sleep(1)
	element.send_keys(Keys.RETURN)
	time.sleep(1)

def reportToHipchat(driver, message, url, usr, passwd, designatedRooms, mainRoom, notificationOnlyMessage):
	
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
	driver.implicitly_wait(10)
	
	#select room
	for room in designatedRooms:
		driver.get(room)
		#wait for web app to load
		time.sleep(5)
		
		#enter message
		xpath = '//*[@id="hc-message-input"]'
		if room == mainRoom:
			enterMessage(driver, xpath, notificationOnlyMessage)
		else:
			enterMessage(driver, xpath, message)
		
		
def listJiraTickets (driver, url, specificBranch):
	driver.get(driver.current_url + '/commit')
	maxHtmlElements = len(driver.find_elements_by_xpath('//*[@id="fullChanges"]/div/ul/li'))
	print('Number of tickets: ' + str(maxHtmlElements))
	ticketCount = 1
	message = ""
	ticketFound = False
	while ticketCount <= maxHtmlElements:
		xpath = '//*[@id="fullChanges"]/div/ul/li['+str(ticketCount)+']/p/a'
		xpath2 = '//*[@id="fullChanges"]/div/ul/li['+str(ticketCount)+']/p'
		try:
			ticket = driver.find_element_by_xpath(xpath)
			ticketFound = True
		except:
			ticketFound = False
		if ticketFound:
			descriptionElement = driver.find_element_by_xpath(xpath2)
			descriptionMatch = re.search('\](.*)', descriptionElement.text)
			description = descriptionMatch.group()
			description = description[2:]
			message += (ticket.get_attribute('data-issue-key') + '\n' +
						' Link - ' + ticket.get_attribute('href') + '\n' +
						'Description - ' + description + '\n' +
						'-------------------------------------------------'
						)
		ticketCount += 1
	return message
	#'//*[@id="fullChanges"]/div/ul/li[1]/p/text()[4]'
	#'//*[@id="fullChanges"]/div/ul/li[1]/p/text()[4]'
	#//*[@id="fullChanges"]/div/ul/li[1]/p/text()[1]

def beginMonitoring (env):
	
	driver = webdriver.Chrome(env.driverPaths['Chrome'])
	
	waitForDeployment = True #no way to end for now
	
	loggedIn = False
	
	while waitForDeployment:
	
		driver.get(env.url['branch']) #list of branches
	
		if not loggedIn:
			login(driver,env.usr['jira'],env.passwd)
			loggedIn = True
		
		branchFound = False
		while not branchFound:
			xpath='//*[@id="buildResultsTable"]/tbody/tr[1]/td[1]/a'#first branch in list - element containing id
			element = driver.find_element_by_xpath(xpath) #assumes there is at least one branch in list
			id = element.get_attribute('id')
			if id != env.lastBranchDeployed:
				env.lastBranchDeployed = id
				xpath='//*[@id="buildResultsTable"]/tbody/tr[1]/td[1]'#element above to be clicked
				driver.find_element_by_xpath(xpath).click() # go to branch details
				branchFound = True
				print('found new branch: ' + env.lastBranchDeployed)
				f = open('data', 'w') #write
				f.write(env.lastBranchDeployed)	
			else:
				print('still looking for new branch...')
				driver.get(driver.current_url)
				time.sleep(10)
			
		found = False
		while not found:
			try: #find branch success/not successful tag
				element = WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[2]/div/section[2]/div/div/div/div[1]/div[2]/div/div[1]/table/tbody/tr/td[2]/span'))
			)
			except:
				print('Cannot find success tag to even determine success or not')
				driver.quit()
			#see if tag says yes or not
			if element.text == 'SUCCESS':
				print('success!')
				found = True
			time.sleep(1)
			driver.get(driver.current_url)
		#after success found then a message is posted to hipchat6
		specificBranch = env.lastBranchDeployed.lstrip('buildResult_')
		notificationOnlyMessage = (env.message + ' ' + specificBranch + '\n' + 
								'-------------------------------------------------')
		env.message += (' ' + specificBranch + '\n' + 
								'-------------------------------------------------')
		env.message += listJiraTickets(driver, env.url, specificBranch)
		reportToHipchat(driver, env.message, env.url['hipchat'], env.usr['hipchat'], env.passwd, env.designatedRooms, env.mainRoom, notificationOnlyMessage)
		if env.login:
			os.chdir(env.loginScriptLocation)
			os.system('python CCA_autologin.py ' + env.loginArgs)