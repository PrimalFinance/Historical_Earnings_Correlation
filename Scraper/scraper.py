import csv
import pandas as pd
import datetime as dt

# Finance Data
import yfinance as yf

# Webscraping 
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from itertools import zip_longest



chrome_driver = "D:\\ChromeDriver\\chromedriver.exe"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")



class StockScraper:
    def __init__(self, ticker: str) -> None:

        self.ticker = ticker.upper()

        # The SEC website uses dashes for some tickers, while Yahoo uses periods. This will switch them. Ex: BRK.B -> BRK-B
        if "." in self.ticker:
            self.ticker = self.ticker.replace(".","-")

        self.sec_quarterly_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=10-q&dateb=&owner=include&count=100&search_text="
        self.sec_annual_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=10-k&dateb=&owner=include&count=100&search_text="
        self.csv_file = self.ticker + f".csv"
        self.file_path = f"D:\\Coding\\VisualStudioCode\\Projects\\Python\\Historical_Earnings_Correlation\\Filing_Records\\" + self.csv_file
        
        self.filing_data = {}
        self.stock_data = pd.DataFrame()
        
    '''----------------------------------- Yahoo Data -----------------------------------'''
    '''-----------------------------------'''
    def set_stock_data(self, period: str = "Max") -> None:
        self.stock_data = yf.download(self.ticker, period=period)
    
    '''-----------------------------------'''
    def get_stock_data(self) -> pd.DataFrame:
        if self.stock_data.empty:
            self.set_stock_data()
        return self.stock_data
    '''-----------------------------------'''
    '''----------------------------------- SEC Data -----------------------------------'''
    '''-----------------------------------'''
    def set_filing_data(self, f_type: str = "10-Q", year_cutoff: int = 2000) -> None:
        
        # Allowable parameters
        quarterly_paramters = ["10-Q", "10-q", "Quarterly", "quarterly", "Q", "q"]
        annual_parameters = ["10-K", "10-k", "Annual", "annual", "Y", "y", "K", "k"]
        price_data = self.get_stock_data()
        

        # Create a browser object
        if f_type in quarterly_paramters:
            self.create_browser()
        elif f_type in annual_parameters:
            self.create_browser(self.sec_annual_url)

        
        # Loop control.
        running = True
        filing_index = 2
        date_index = 2
        
        while running:

            try:
                filing = {"Filing Type": "",
                        "Filing Date": ""}
                # Xpaths to the elements.
                
                filing_type_xpath = f"/html/body/div[4]/div[4]/table/tbody/tr[{filing_index}]/td[1]"
                date_xpath = f"/html/body/div[4]/div[4]/table/tbody/tr[{date_index}]/td[4]"
                # Extract the data.
                filing_type = self.read_data(filing_type_xpath)
                filing_date = self.read_data(date_xpath)

                # Split the filing date to get the year.
                year, month, day = filing_date.split("-")

                
                # We only want the filing dates of 10-q not any ammendments like 10-Q/A. 
                if filing_type == "10-Q" or filing_type == "10-K":
                    # If we want to cutoff at the year 2000, it will not collect any years prior. 
                    if int(year) < year_cutoff:
                        pass
                    else:

                        # Set the filing date and type based off the data from the scraper.
                        filing["Filing Type"] = filing_type
                        filing["Filing Date"] = filing_date


                        try:
                            price = price_data.loc[filing_date]["Adj Close"]
                            index_at_date = self.get_index(filing_date, price_data)
                            # Get the next price by taking the index of the current row and adding 1.
                            try:
                                next_price = price_data.iloc[index_at_date+1]["Adj Close"]
                                # Calculate the percent change between the price at close, and the following days price at close. Note: the first price at close is based off of when a form is filed. 
                                percent_change = round(((next_price/price) - 1) * 100,2)
                                filing["1d % Change"] = percent_change
                            except IndexError:
                                next_price = "N/A"
                                filing["1d % Change"] = "N/A"

                            # Get the price after 1 week.
                            try:
                                next_week_price = price_data.iloc[index_at_date+5]["Adj Close"]
                                week_percent_change = round(((next_week_price/price) - 1) * 100,2)
                                filing["1w % Change"] = week_percent_change
                            except IndexError:
                                next_week_price = "N/A"
                                filing["1w % Change"] = "N/A"

                            # Format the price to save it. 
                            try:
                                price = round(price, 3)
                            except TypeError:
                                pass
                            try:
                                next_price = round(next_price, 3)
                            except TypeError:
                                pass
                            try:
                                next_week_price = round(next_week_price, 3)
                            except TypeError:
                                pass
                            filing["Price"] = price
                            filing["Next Price"] = next_price
                            filing["Next Week Price"] = next_week_price
                        except KeyError:
                            new_date = self.find_next_trading_day(filing_date, price_data)
                            price = price_data.loc[new_date]["Adj Close"]
                            # Gets the index of the row that matches the date.
                            index_at_date = self.get_index(new_date, price_data)

                            # Get the next price by taking the index of the current row.
                            try:
                                next_price = price_data.iloc[index_at_date+1]["Adj Close"]
                                percent_change = round(((next_price/price) - 1) * 100,2)
                                filing["1d % Change"] = percent_change
                            except IndexError:
                                next_price = "N/A"
                                filing["1d % Change"] = "N/A"

                            # Get the price after 1 week.
                            try:
                                next_week_price = price_data.iloc[index_at_date+5]["Adj Close"]
                                week_percent_change = round(((next_week_price/price) - 1) * 100,2)
                                filing["1w % Change"] = week_percent_change
                            except IndexError:
                                next_week_price = "N/A"
                                filing["1w % Change"] = "N/A"
                            
                            # Format the price to save it. 
                            try:
                                price = round(price, 3)
                            except TypeError:
                                pass
                            try:
                                next_price = round(next_price, 3)
                            except TypeError:
                                pass
                            try:
                                next_week_price = round(next_week_price, 3)
                            except TypeError:
                                pass
                            filing["Price"] = price
                            filing["Next Price"] = next_price
                            filing["Next Week Price"] = next_week_price

                        try:
                            self.filing_data[year].append(filing)
                        except KeyError:
                            self.filing_data[year] = [filing]


                filing_index += 1
                date_index += 1
            except NoSuchElementException:
                running = False
      
        # Sort the data, so each year will have the quarters in order. In descending order from Q4 -> Q1.
        for key, val in self.filing_data.items():
            self.filing_data[key] = sorted(val, key=lambda x: x['Filing Date'], reverse=True)
        
        # Sort the years.
        self.filing_data = dict(sorted(self.filing_data.items(),reverse=True))
    
        # Insert the filings into a csv file. 
        self.write_to_csv()
            

    '''-----------------------------------'''
    def get_filing_data(self) -> dict:
        # Check if there is an existing CSV file. 
        update_needed = self.is_update_needed()

        if update_needed:
            if self.filing_data == {}:
                self.set_filing_data(f_type="10-Q")
                self.set_filing_data(f_type="10-K")
        
        elif not update_needed:
            self.read_from_csv()
        
        return self.filing_data
    
    '''----------------------------------- CSV Utilities -----------------------------------'''
    '''-----------------------------------'''
    def write_to_csv(self):
        with open (self.file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Filing Date', 'Filing Type',"Price", "Next Price", "1d % Change", "Next Week Price", "1w % Change"])
            for key, val in self.filing_data.items():
                for i in val:
                    writer.writerow([i['Filing Date'], i['Filing Type'], i["Price"], i["Next Price"], i["1d % Change"], i["Next Week Price"], i['1w % Change']])

    '''-----------------------------------'''
    def read_from_csv(self):

        with open(self.file_path, 'r') as file:
            # Read the data into csv.reader object.
            reader = csv.reader(file)
            # Skip the header.
            next(reader)
            for row in reader:
                filing_date, filing_type, price, next_price, percent_change, next_week_price, week_percent_change = row

                filing = {"Filing Date": filing_date,
                          "Filing Type": filing_type,
                          "Price": price,
                          "Next Price": next_price,
                          "1d % Change": percent_change,
                          "Next Week Price": next_week_price,
                          "1w % Change": week_percent_change}
                
                year, month, day = filing_date.split("-")

                try:
                    self.filing_data[year].append(filing)
                except KeyError:
                    self.filing_data[year] = [filing]


    '''-----------------------------------'''
    def is_update_needed(self, month_diff: int = 6) -> bool:
        '''
        month_diff: The number of allowed months between the most recent filing date and the current date.
                    If there is a larger difference than specified, the function will return True, indicating an update is needed
        '''

        try:
            # Open the csv file to read the data. 
            with open(self.file_path, 'r') as file:
                # Read the data into csv.reader object.
                reader = csv.reader(file)

                # Skip the header
                next(reader)
                # Get the most recent entry
                most_recent_entry = next(reader)
                # Get the date from the row. 
                date = most_recent_entry[0]
                # Turn the date into a datetime object so we can perform calculations. 
                date_obj = dt.datetime.strptime(date, "%Y-%m-%d")
                cur_date = dt.datetime.now().date()

                # Calculate the difference in months.
                difference = (cur_date.year - date_obj.year) * 12 + (cur_date.month - date_obj.month)

                if difference >= month_diff:
                    return True
                elif difference < month_diff:
                    return False
        # If the file does not exist, it means the scraper has not searched for it yet. Therefore an update is needed.
        except FileNotFoundError: 
            return True
        # The iteration is typically stopped because there is no data in the file. Therefore the scraper needs to update it. 
        except StopIteration:
            return True
            
    '''-----------------------------------'''
    '''----------------------------------- Browser Utilities -----------------------------------'''

    def create_browser(self, url=None):
        '''
        :param url: The website to visit.
        :return: None
        '''
        self.browser = webdriver.Chrome(
            executable_path=chrome_driver, chrome_options=chrome_options)
        # Default browser route
        if url == None:
            self.browser.get(url=self.sec_quarterly_url)
        # External browser route
        else:
            self.browser.get(url=url)

    '''-----------------------------------'''
    def read_data(self, xpath: str):
        '''
        :param browser: Selenium browser object.
        :return: None
        '''

        data = self.browser.find_element("xpath", xpath).text
        return data
    
    '''----------------------------------- Python Utilities -----------------------------------'''
    '''--------------------------------------'''
    def get_index(self, date: str, data) -> int:
        index = 0
        for d in data.iterrows():
            df_date = str(d[0]).split(" ")[0]

            if date == df_date:
                return index
            index += 1

    '''--------------------------------------'''
    # Sometimes companies will file their reports on a non-trading day. 
    # So we will keep adding to the date until we find the next trading day
    def find_next_trading_day(self, filing_date, data):

        running = True
        index = 1
        # Turn date into datetime object so we can add to it. 
        date_obj = dt.datetime.strptime(filing_date, "%Y-%m-%d")
        
        while running:
            new_date_obj = date_obj + dt.timedelta(days=index)

            new_date_str = new_date_obj.strftime("%Y-%m-%d")
            # Try to access the trading day. If it does not exist, continue on.
            try:
                data = data.loc[new_date_str]
                return new_date_str
            except KeyError:
                pass
            index += 1
