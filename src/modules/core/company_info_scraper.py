import src.parameters as parameters
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv


class CompanyInfoScraper:
	def __init__(self, companies, file, is_clean_run, already_scraped_companies_list):
		self.file = file
		self.companies = companies
		self.writer = csv.writer(self.file)
		self.already_scraped_companies_list = already_scraped_companies_list

		if is_clean_run:
			self.writer.writerow([
				'company', 'company_size', 'industry', 'type', 'founded', 'specialities',
				'linkedin_url', 'about_url', 'website'])
			file.flush()

		options = webdriver.ChromeOptions()
		options.add_argument("--disable-blink-features")
		options.add_argument("--disable-blink-features=AutomationControlled")
		self.driver = webdriver.Chrome(executable_path='chromedriver', options=options)

		print('Logging into linkedin...')
		self.driver.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

		username_input = self.driver.find_element_by_name('session_key')
		username_input.send_keys(parameters.linkedin_username)

		password_input = self.driver.find_element_by_name('session_password')
		password_input.send_keys(parameters.linkedin_password)

		# click on the sign in button
		# we're finding Sign in text button as it seems this element is seldom to be changed
		self.driver.find_element_by_xpath('//button[text()="' + parameters.linkedin_sign_in_button_text + '"]').click()
		# version of linkedin

	def scrape_companies(self):
		"""
		scrapes linkedin companies with the help of selenium and webdriver
		:return:
		"""
		for index, row in self.companies.iterrows():
			company_name = row['Company']
			if company_name in self.already_scraped_companies_list:
				print(company_name + ' already scraped...')
				continue
			company_profiles = self.get_google_first_page_company_result(company_name)

			if len(company_profiles) == 0:
				page_source = self.driver.page_source
				if parameters.google_empty_result_page_identifier in page_source:
					self.write_empty_row(company_name)
					continue
				print('Getting blocked by google...terminating')
				time.sleep(15)
				self.clean()
				raise SystemExit(0)

			for count, company_profile in enumerate(company_profiles):
				if 'https://www.linkedin.com/company/' in company_profile:
					try:
						print('Scraping linkedin page: ' + company_profile)
						company_about_url = company_profile + '/about'
						self.driver.get(company_about_url)
						sel = Selector(text=self.driver.page_source)
						possible_website_urls = sel\
							.xpath('//*[contains(@class, "link-without-visited-state")]/text()') \
							.extract()
						company_size = sel \
							.xpath('//*[contains(@class, "org-about-company-module__company-size-definition-text")]/text()') \
							.extract_first()
						if company_size:
							company_size = company_size.strip()
						else:
							company_size = ''

						company_details = sel \
							.xpath('//*[contains(@class, "org-page-details__definition-text t-14 t-black--light t-normal")]/text()') \
							.extract()
						website_url = ''
						for possible_website_url in possible_website_urls:
							if 'www' in possible_website_url:
								website_url = possible_website_url

						print('writing results...')
						company_details_stripped = self.strip_company_details_linkedin(company_details)

						self.writer.writerow([
							company_name, company_size, company_details_stripped['industry'],
							company_details_stripped['type'], company_details_stripped['founded'],
							company_details_stripped['specialities'], company_profile,
							company_about_url, website_url])
						self.file.flush()
						break
					except Exception as e:
						print(company_profile + " --> failed: " + str(e))
				if count + 1 == len(company_profiles):
					self.write_empty_row(company_name)

			print('sleeping for 15 secs..')
			time.sleep(15)

	@staticmethod
	def strip_company_details_linkedin(company_details):
		try:
			industry = company_details[2].strip()
		except:
			industry = ''
		try:
			type = company_details[3].strip()
		except:
			type = ''
		try:
			founded = company_details[4].strip()
		except:
			founded = ''
		try:
			specialities = company_details[5].strip()
		except:
			specialities = ''

		return {
			'industry': industry,
			'type': type,
			'founded': founded,
			'specialities': specialities
		}

	def get_google_first_page_company_result(self, company_name):
		try:
			print('Searching Google for : ' + company_name)
			self.driver.get('https://www.google.com/')

			search_input = self.driver.find_element_by_name('q')
			search_input.send_keys('site:linkedin.com/ AND "' + company_name + '" AND "about"')

			search_input.send_keys(Keys.RETURN)

			print('Scraping possible results...')
			# grab all linkedin companies profiles from first page at Google
			company_profiles = self.driver.find_elements_by_xpath('//*[@class="r"]/a[1]')
			company_profiles = [profile.get_attribute('href') for profile in company_profiles]

			return company_profiles
		except Exception as e:
			print("An error occurred while searching google: " + str(e))

	def clean(self):
		self.driver.quit()
		self.file.close()
		print('Finished!')

	def write_empty_row(self, company_name):
		self.writer.writerow([
			company_name, '', '',
			'', '', '', '', '', ''])
		self.file.flush()
