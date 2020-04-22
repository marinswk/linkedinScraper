import pandas as pd
import os
from src.modules.core.company_info_scraper import CompanyInfoScraper
from src.parameters import scrape_results_file_path, companies_to_scrape_file_path

if __name__ == "__main__":
	"""
	Initializes the csv files with the company list to scrape and the already scraped ones if exist
	and continues from the last scraped company in the list
	"""
	companies = pd.read_csv(companies_to_scrape_file_path)
	file = open(scrape_results_file_path, 'a+', newline='')
	is_clean_run = True
	already_scraped_companies_list = []
	if not os.stat(scrape_results_file_path).st_size == 0:
		results_df = pd.read_csv(scrape_results_file_path, encoding='latin-1')
		already_scraped_companies_list = results_df['company'].tolist()
		is_clean_run = False
	company_info_scraper = CompanyInfoScraper(companies, file, is_clean_run, already_scraped_companies_list)
	company_info_scraper.scrape_companies()
	company_info_scraper.clean()
