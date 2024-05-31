import time
import base64
import hashlib
import hmac
import json
import urllib.request as urllib2
import urllib.parse as urllib
import ssl


class cfApiMethods(object):
    def __init__(self, apiPath, apiPublicKey="", 
                    apiPrivateKey="", timeout=10, checkCertificate=True, useNonce=False):
        self.apiPath = apiPath
        self.apiPublicKey = apiPublicKey
        self.apiPrivateKey = apiPrivateKey
        self.timeout = timeout
        self.nonce = 0
        self.checkCertificate = checkCertificate
        self.useNonce = useNonce

    ##### public endpoints #####

    # returns all instruments with specifications
    def get_instruments(self):
        endpoint = "/derivatives/api/v3/instruments"
        return self.make_request("GET", endpoint)

    # returns market data for all instruments
    def get_tickers(self):
        endpoint = "/derivatives/api/v3/tickers"
        return self.make_request("GET", endpoint)


    # returns the entire order book of a futures
    def get_orderbook(self, symbol):
        endpoint = "/derivatives/api/v3/orderbook"
        postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns historical data for futures and indices
    def get_history(self, symbol, lastTime=""):
        endpoint = "/derivatives/api/v3/history"
        if lastTime != "":
            postUrl = "symbol=%s&lastTime=%s" % (symbol, lastTime)
        else:
            postUrl = "symbol=%s" % symbol
        return self.make_request("GET", endpoint, postUrl=postUrl)

    ##### private endpoints #####

    # returns key account information
    # Deprecated because it returns info about the Futures margin account

    # returns key account information
    def get_accounts(self):
        endpoint = "/derivatives/api/v3/accounts"
        return self.make_request("GET", endpoint)

    # places an order
    def send_order(self, orderType, symbol, side, size, limitPrice, stopPrice=None, clientOrderId=None):
        endpoint = "/derivatives/api/v3/sendorder"
        postBody = "orderType=%s&symbol=%s&side=%s&size=%s&limitPrice=%s" % (
            orderType, symbol, side, size, limitPrice)

        if orderType == "stp" and stopPrice is not None:
            postBody += "&stopPrice=%s" % stopPrice

        if clientOrderId is not None:
            postBody += "&cliOrdId=%s" % clientOrderId

        return self.make_request("POST", endpoint, postBody=postBody)

    # returns filled orders
    def get_fills(self, lastFillTime=""):
        endpoint = "/derivatives/api/v3/fills"
        if lastFillTime != "":
            postUrl = "lastFillTime=%s" % lastFillTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns all open positions
    def get_openpositions(self):
        endpoint = "/derivatives/api/v3/openpositions"
        return self.make_request("GET", endpoint)

    # sends an xbt withdrawal request
    def send_withdrawal(self, targetAddress, currency, amount):
        endpoint = "/derivatives/api/v3/withdrawal"
        postBody = "targetAddress=%s&currency=%s&amount=%s" % (
            targetAddress, currency, amount)
        return self.make_request("POST", endpoint, postBody=postBody)

    # returns xbt transfers
    def get_transfers(self, lastTransferTime=""):
        endpoint = "/derivatives/api/v3/transfers"
        if lastTransferTime != "":
            postUrl = "lastTransferTime=%s" % lastTransferTime
        else:
            postUrl = ""
        return self.make_request("GET", endpoint, postUrl=postUrl)

    # returns all notifications
    def get_notifications(self):
        endpoint = "/derivatives/api/v3/notifications"
        return self.make_request("GET", endpoint)

    # makes an internal transfer
    def transfer(self, fromAccount, toAccount, unit, amount):
        endpoint = "/derivatives/api/v3/transfer"
        postBody = "fromAccount=%s&toAccount=%s&unit=%s&amount=%s" % (
            fromAccount, toAccount, unit, amount)
        return self.make_request("POST", endpoint, postBody=postBody)

    # accountlog csv
    def get_accountlog(self):
        endpoint = "/api/history/v2/accountlogcsv"
        return self.make_request("GET", endpoint)

    def _get_partial_historical_elements(self, elementType, **params):
        endpoint = "/api/history/v2/%s" % elementType

        params = {k: v for k, v in params.items() if v is not None}
        postUrl = urllib.urlencode(params)

        return self.make_request_raw("GET", endpoint, postUrl)

    def _get_historical_elements(self, elementType, since=None, before=None, sort=None, limit=1000):
        elements = []

        continuationToken = None

        while True:
            res = self._get_partial_historical_elements(elementType, since = since, before = before, sort = sort, continuationToken = continuationToken)
            body = json.loads(res.read().decode('utf-8'))
            elements = elements + body['elements']

            if res.headers['is-truncated'] is None or res.headers['is-truncated'] == "false":
                continuationToken = None
                break
            else:
                continuationToken = res.headers['next-continuation-token']

            if len(elements) >= limit:
                elements = elements[:limit]
                break

        return elements

    def get_orders(self, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves orders of your account. With default parameters it gets the 1000 newest orders.

        :param since: Timestamp in milliseconds. Retrieves orders starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves orders before this time.
        :param sort: String "asc" or "desc". The sorting of orders.
        :param limit: Amount of orders to be retrieved.
        :return: List of orders
        """

        return self._get_historical_elements('orders', since, before, sort, limit)

    def get_executions(self, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves executions of your account. With default parameters it gets the 1000 newest executions.

        :param since: Timestamp in milliseconds. Retrieves executions starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves executions before this time.
        :param sort: String "asc" or "desc". The sorting of executions.
        :param limit: Amount of executions to be retrieved.
        :return: List of executions
        """

        return self._get_historical_elements('executions', since, before, sort, limit)

    def get_market_price(self, symbol, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves prices of given symbol. With default parameters it gets the 1000 newest prices.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves prices starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves prices before this time.
        :param sort: String "asc" or "desc". The sorting of prices.
        :param limit: Amount of prices to be retrieved.
        :return: List of prices
        """

        return self._get_historical_elements('market/' + symbol + '/price', since, before, sort, limit)

    def get_market_orders(self, symbol, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves orders of given symbol. With default parameters it gets the 1000 newest orders.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves orders starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves orders before this time.
        :param sort: String "asc" or "desc". The sorting of orders.
        :param limit: Amount of orders to be retrieved.
        :return: List of orders
        """

        return self._get_historical_elements('market/' + symbol + '/orders', since, before, sort, limit)

    def get_market_executions(self, symbol, since=None, before=None, sort=None, limit=1000):
        """
        Retrieves executions of given symbol. With default parameters it gets the 1000 newest executions.

        :param symbol: Name of a symbol. For example "PI_XBTUSD".
        :param since: Timestamp in milliseconds. Retrieves executions starting at this time rather than the newest/latest.
        :param before: Timestamp in milliseconds. Retrieves executions before this time.
        :param sort: String "asc" or "desc". The sorting of executions.
        :param limit: Amount of executions to be retrieved.
        :return: List of executions
        """

        return self._get_historical_elements('market/' + symbol + '/executions', since, before, sort, limit)

    # signs a message
    def sign_message(self, endpoint, postData, nonce=""):
        if endpoint.startswith('/derivatives'):
            endpoint = endpoint[len('/derivatives'):]

        # step 1: concatenate postData, nonce + endpoint
        message = postData + nonce + endpoint

        # step 2: hash the result of step 1 with SHA256
        sha256_hash = hashlib.sha256()
        sha256_hash.update(message.encode('utf8'))
        hash_digest = sha256_hash.digest()

        # step 3: base64 decode apiPrivateKey
        secretDecoded = base64.b64decode(self.apiPrivateKey)

        # step 4: use result of step 3 to has the result of step 2 with HMAC-SHA512
        hmac_digest = hmac.new(secretDecoded, hash_digest, hashlib.sha512).digest()

        # step 5: base64 encode the result of step 4 and return
        return base64.b64encode(hmac_digest)

    # creates a unique nonce
    def get_nonce(self):
        # https://en.wikipedia.org/wiki/Modulo_operation
        self.nonce = (self.nonce + 1) & 8191
        return str(int(time.time() * 1000)) + str(self.nonce).zfill(4)

    # sends an HTTP request
    def make_request_raw(self, requestType, endpoint, postUrl="", postBody=""):
        # create authentication headers
        postData = postUrl + postBody

        if self.useNonce:
            nonce = self.get_nonce()
            signature = self.sign_message(endpoint, postData, nonce=nonce)
            authentHeaders = {"APIKey": self.apiPublicKey,
                              "Nonce": nonce, "Authent": signature}
        else:
            signature = self.sign_message(endpoint, postData)
            authentHeaders = {
                "APIKey": self.apiPublicKey, "Authent": signature}

        authentHeaders["User-Agent"] = "cf-api-python/1.0"

        # create request
        if postUrl != "":
            url = self.apiPath + endpoint + "?" + postUrl
        else:
            url = self.apiPath + endpoint

        request = urllib2.Request(url, str.encode(postBody), authentHeaders)
        request.get_method = lambda: requestType

        # read response
        if self.checkCertificate:
            response = urllib2.urlopen(request, timeout=self.timeout)
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib2.urlopen(
                request, context=ctx, timeout=self.timeout)

        # return
        return response

    # sends an HTTP request and read response body
    def make_request(self, requestType, endpoint, postUrl="", postBody=""):
        return self.make_request_raw(requestType, endpoint, postUrl, postBody).read().decode("utf-8")
    
# First, you need to create an instance of cfApiMethods
api = cfApiMethods(apiPath="https://demo-futures.kraken.com", 
                    apiPublicKey="D8d22EHn6x7iDUtZ++cF95PUNnblxsN3jQct2/+0lELlV+9lkjk0id4N", 
                    apiPrivateKey="JPisYm9qvwvgvPjx1vvrvYYAVj+B2KGAqXRMDLUXrX3muoYu9YHu2/qikgj4f1QOGjo2ImMOueF/FBXGdr8ht+tj")

# print(api.get_tickers())


# data=json.loads(api.get_accounts())
# balances = {}
# for account_name, account_data in data["accounts"].items():
#     if account_name.startswith("fi_") or account_name.startswith("fv_"):
#         for currency, balance in account_data["balances"].items():
#             print(currency)
#             if currency in balances:
#                 balances[currency] += balance
#             else:
#                 balances[currency] = balance

# print(balances)


# api2 = cfApiMethods(apiPath="https://demo-futures.kraken.com", 
#                     apiPublicKey="R3zI9WWUfuwDHiCJ+6+JO9yLiOXnymLn9bVvhhskrE//0AMG04WPlkWF", 
#                     apiPrivateKey="Q8hf1Yf47nUWhwwtw+icVZ2KVM55rVSEPKsq+eS3rch6sAznzA2HuFqptra+G3Q0jdvB2B3Poiud5M5QisBNeJyy")

# print(api2.get_accounts())