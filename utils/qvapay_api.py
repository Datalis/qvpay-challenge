import datetime
import requests
import json
import threading
from common.var import COINS

class QvaPay:
    def __init__(self):
        # data for scraping
        self.base_url = "https://qvapay.com/api/p2p?page={number}"
        self.response = requests.get(self.base_url.format(number=1))
        self.data = json.loads(self.response.text)
        self.num_pages = self.data["last_page"]
        # simulating db
        # table order
        self.db_orders = {}
        #table user
        self.db_users = {}
        # structure to chache a query
        self.user_coin_query = {}
        # to avoid race conditions while threading
        self.lock = threading.Lock()
        

    def get_data(self, page: int) -> list:
        """
        Gets the data of a single page and saves it to the DB.

        Parameters
        ----------
        page : Number of the page to get the data from (expected to be an int).
        
        Returns
        -------
        `void`
        """
        data = requests.get(self.base_url.format(number=page))
        data_json = json.loads(data.text)
        for i in range(len(data_json["data"])):
            uuid = data_json["data"][i]["uuid"]
            user_uuid = data_json["data"][i]["owner"]["uuid"]
            coin = data_json["data"][i]["coin"]
            amount = float(data_json["data"][i]["amount"])
            with self.lock:
                # add the data to the table order in the db
                self.db_orders[uuid] = data_json["data"][i]
                # add the data to the user_coin query
                if user_uuid in self.db_users:
                    self.user_coin_query[user_uuid][coin] += amount
                    self.user_coin_query[user_uuid]["all"] += amount
                else:
                    self.user_coin_query[user_uuid] = {coins:0.0 for coins in COINS}
                    self.user_coin_query[user_uuid]["all"] = 0.0 
                    self.user_coin_query[user_uuid][coin] = amount
                    # add the data to the user table in the db
                    self.db_users[user_uuid] = data_json["data"][i]["owner"]    

    def update_db(self):
        """
        Update the entries of the DB
        """
        threads = []
        for i in range(self.num_pages): 
            thread = threading.Thread(target=self.get_data, args=(i,)) 
            threads.append(thread) 
            thread.start() 
        for thread in threads: 
            thread.join() 

    def __get_date(self, db_order_entry: dict) -> datetime.time:
        """
        Helper method to get the date of the DB entrie as a datetime.date object
        """
        year = int(db_order_entry["updated_at"][:4])
        month = int(db_order_entry["updated_at"][5:7])
        day = int(db_order_entry["updated_at"][8:10])
        return datetime.date(year, month, day)

    def __is_date_in(self, current: datetime.date, start: datetime.date,
                      end: datetime.date) -> bool:
        """
        Helper method to check if a given current date is withind the limits given
        """
        return current >= start and current <= end
    
    def get_spread(self, currency: str, start_date: datetime.date,
                    end_date: datetime.date) -> tuple:
        """
        Gets the spread of all orders of a given coin from within two dates
        """
        ask = None
        bid = None
        for value in self.db_orders.values():
            current = self.__get_date(db_order_entry=value)
            rate = float(value["amount"]) / float(value["receive"])
            if value["coin"] == currency and self.__is_date_in(current, start_date, end_date):    
                if value["type"] == "buy":
                    if ask is not None:
                        ask = rate if rate < ask else ask
                    else:
                        ask = rate
                elif value["type"] == "sell":
                    if bid is not None:
                        bid = rate if rate > bid else bid
                    else:
                        bid = rate
        return bid, ask

    def get_supply(self, currency: str, start_date: datetime.date,
                    end_date: datetime.date) -> tuple:
        """
        Gets the total demand and offer of a given coin from within two dates.
        """
        oferta = 0.0
        demanda = 0.0
        for order in self.db_orders.values():
            current = self.__get_date(db_order_entry=order)
            if order["coin"] == currency and self.__is_date_in(current, start_date, end_date):
                if order["type"] == "buy":
                    oferta += float(order["amount"])
                if order["type"] == "sell":
                    demanda += float(order["amount"])
        return oferta, demanda
    
    def get_users_info_by_id(self, users_id: str) -> list:
        """
        Get the users info by the uuid
        """
        return [self.db_users[uuid] for uuid in users_id]

    def get_market_makers(self, top: int, coin: str) -> tuple:
        """
        Gets the uuid of the top market makers
        """
        list_users = [*self.user_coin_query.items()]
        list_users.sort(key=lambda x: x[1][coin])
        data = list_users[-top:] 
        return [user[0] for user in data]
    
    def get_market_makers_spread(self, top: int, coin: str, start: datetime.date,
                                  end: datetime.date) -> list:
        """
        Gets the market makers spread of a given coin by date
        from within two dates
        """
        date_order_query = {}
        market_makers_uuid = self.get_market_makers(top, coin)
        for key, order in self.db_orders.items():
            date = self.__get_date(db_order_entry=order)
            rate = float(order["amount"]) / float(order["receive"])
            # validar ofertas de interes
            if order["owner"]["uuid"] in market_makers_uuid and order["coin"] == coin and self.__is_date_in(date, start, end):
                if date in date_order_query:
                    if order["type"] == "sell":
                        if date_order_query[date]["bid"] != None and rate > date_order_query[date]["bid"]:
                            date_order_query[date]["bid"] = rate
                        else:
                            date_order_query[date]["bid"] = rate
                    else:
                        if date_order_query[date]["ask"] != None and rate < date_order_query[date]["ask"]:
                            date_order_query[date]["ask"] = rate
                        else:
                            date_order_query[date]["ask"] = rate
                else:
                    if order["type"] == "buy":
                        date_order_query[date] = {"bid": rate, "ask":None}
                    else:
                        date_order_query[date] = {"ask": rate, "bid":None}  
        sorted_list = sorted([*date_order_query.items()], key=lambda x: x[0])
        for index, (date, spread) in enumerate(sorted_list):
            if spread["ask"] == None or spread["bid"]== None:
                del sorted_list[index]
        return sorted_list