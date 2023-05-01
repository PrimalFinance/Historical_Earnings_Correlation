import datetime as dt


class Pair:
    def __init__(self, t1: str, t2: str, d1: dict, d2: dict) -> None:
        # First ticker.
        self.t1 = t1
        # Second ticker.
        self.t2 = t2
        # First data related to ticker1.
        self.d1 = d1
        # Second data related to ticker2.
        self.d2 = d2
        # The title of the pair. Ex: "KO" - "PEP"
        self.pair = f"{self.t1} - {self.t2}"
        # The markers between the pairs. Markers are when earnings are within 1 day of eachother. 
        self.pair_markers = []

        # The relationship in price between companies during a marker period.
        self.total_pos = 0
        self.total_neg = 0
        self.perc_pos = 0
        self.perc_neg = 0
        self.total_markers = 0

        # Lenghts of the data.
        d1_length = len(list(self.d1.keys()))
        d2_length = len(list(self.d2.keys()))

        # Sometimes there will be cases where one company has been around for more years. 
        # Therefore we compare how long each one has traded for. We take the shorter length so we can compare both fully. 
        if d1_length > d2_length:
            self.years_to_compare = list(self.d2.keys())
        elif d1_length < d2_length:
            self.years_to_compare = list(self.d1.keys())
        elif d1_length == d2_length:
            self.years_to_compare = list(self.d1.keys())

        # Sort the years so they are in order.
        self.years_to_compare = sorted(self.years_to_compare)
        self.years_searched = f"{self.years_to_compare[0]} - {self.years_to_compare[-1]}"
        self.num_of_years = len(self.years_to_compare)

    '''-----------------------------------'''
    def generate_markers(self):
        
        for y in self.years_to_compare:

            for i in range(len(self.d1[y])):
                try:
                    date1 = self.d1[y][i]["Filing Date"]
                    date2 = self.d2[y][i]["Filing Date"]

                    difference = self.date_differences(date1, date2)

                    if difference == 1:
                        
                        marker = {"Date1": date1,
                                  "Date2": date2,
                                  "Data1": self.d1[y][i],
                                  "Data2": self.d2[y][i]}
                        self.pair_markers.append(marker)
                except IndexError:
                    pass
            
    '''-----------------------------------'''
    def get_markers(self):
        return self.pair_markers
    '''-----------------------------------'''
    def display_markers(self):
        print(f"------------------------------------")
        for i in self.pair_markers:
            print(f"[{self.pair}]: {i['Date1']}  Pos: {i['Positive Relationship']}   Neg: {i['Negative Relationship']}")
    '''-----------------------------------'''
    def calculate_relationship(self):

        # It is considered positive if the stock price of both companies moved in the same direction with the marker period.  
        positive = 0
        # It is considered negative if the stock price performed opposite of each other in the marker period. 
        negative = 0
        # Invalid markers are usually ones close to the current date. This is because the have not had a trading day, and therefore not enough price data. 
        invalid = 0
        # Get the total number of markers.
        num_markers = len(self.pair_markers)

        for i in self.pair_markers:
            
            try:
                t1_change = float(i["Data1"]["1d % Change"])
                t2_change = float(i["Data2"]["1d % Change"])
                # If both companies increased in price during the marker period.
                if t1_change >= 0 and t2_change >= 0:
                    positive += 1
                # If both companies decreased in price during the marker period.
                elif t1_change < 0 and t2_change < 0:
                    positive += 1
                # If Company 1 increased in price, while Company 2 decreases in price.
                elif t1_change >= 0 and t2_change < 0:
                    negative += 1
                # If Company 1 decreases in price, while Company 2 increases in price.
                elif t1_change < 0 and t2_change >= 0:
                    negative += 1
            except TypeError:
                invalid += 1
            # This error is raised when, one of the % changes is "N/A". 
            except ValueError:
                invalid += 1
            
        self.total_pos = positive
        self.total_neg = negative
        try:
            self.perc_pos = round((positive / (num_markers-invalid)) * 100, 2)
        except ZeroDivisionError:
            self.perc_pos = 0.0
        try:
            self.perc_neg = round((negative / (num_markers-invalid)) * 100, 2) 
        except ZeroDivisionError:
            self.perc_neg = 0.0
        self.total_markers = num_markers - invalid
        
        for i in self.pair_markers:
            pos_rel = round((positive / (num_markers-invalid)) * 100, 2)
            neg_rel = round((negative / (num_markers-invalid)) * 100, 2)
            i["Positive Relationship"] = pos_rel
            i["Negative Relationship"] = neg_rel

    '''-----------------------------------'''
    

    '''----------------------------------- Utilities -----------------------------------'''
    def date_differences(self, date1: str, date2: str):
        date1 = dt.datetime.strptime(date1, "%Y-%m-%d")
        date2 = dt.datetime.strptime(date2, "%Y-%m-%d")

        # We want the "greater" date to avoid negative differences. And chronologically it makes sense to compare the later date to the earlier date. 
        if date1 > date2:
            difference = date1 - date2
        elif date1 < date2:
            difference = date2 - date1
        # If the dates are equal it will result in a difference of 0. 
        elif date1 == date2:
            difference = date1 - date2

        return difference.days
    '''-----------------------------------'''
    
    '''-----------------------------------'''
    '''-----------------------------------'''

        



class EarningsPairs: 
    def __init__(self, data: dict) -> None:
        self.data = data

        # Get all of the tickers
        self.tickers = list(self.data.keys())

        # All of the pairs from the tickers being compared. 
        self.pairs = []

    '''-----------------------------------'''
    def generate_pairs(self) -> list:

        for i in range(len(self.tickers)):
            for j in range(len(self.tickers)):
                if i != j:
                    ticker1 = self.tickers[i]
                    ticker2 = self.tickers[j]
                    ticker_pair = Pair(t1=ticker1, t2=ticker2, d1=self.data[ticker1][0], d2=self.data[ticker2][0])
                    self.pairs.append(ticker_pair)
    
   
        
    '''-----------------------------------'''
    '''-----------------------------------'''
    def organize_pairs(self):
        organized_list = []
        # Organize the list by the amount of markers that have a positive match. 
        organized_list = sorted(self.pairs, key=lambda x: x.perc_pos, reverse=True)

        self.pairs = organized_list

    '''-----------------------------------'''
    def delete_duplicates(self):
        
        indexes_to_delete = []

        # Create a copy of the data. 
        data = self.pairs


        for i in data:

            cur_pair = i.pair

            
            ticker1, ticker2 = cur_pair.replace(" ","").split("-")
            rev_cur_pair  = f"{ticker2} - {ticker1}"

            for j in data:
                
                compare_pair = j.pair

                if cur_pair == compare_pair:
                    pass
                else:
                    if rev_cur_pair == compare_pair:
                        self.pairs.remove(j)

    '''-----------------------------------'''
    def compare_pairs(self):
        for i in self.pairs:
            i.generate_markers()
            i.calculate_relationship()
        
        self.organize_pairs()
        self.delete_duplicates()
        for j in self.pairs:
            print(f"""\n\n-----------------------------
[{j.pair}]
Total Positive: {j.total_pos}
Total Negative: {j.total_neg}
% Positive:  {j.perc_pos}%
Total Markers: {j.total_markers}
Years Searched: {j.years_searched} ({j.num_of_years-1} years)""")

        

    '''-----------------------------------'''
    '''-----------------------------------'''
    '''-----------------------------------'''

        
