class Strategy(): # Strategy no.3: Graville's rules
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 35*60
        self.options = {}

        # User defined constants
        self.buy_ratio = 0.7

        # user defined class attribute
        self.last_type = 'sell' # Last action other than waiting
        self.last_ma_trend = None # Trend of MA at the last period
        self.close_price_trace = np.array([]) # The array of recent prices
        self.ma_short = 20 # Range of coverage of the short MA, in periods
        self.ma_long = 50 # Range of coverage of the long MA, in periods
        self.last_buy = -1 # Last buy price (-1 if waiting to buy)
        self.last_s_ma = None # Value of the short MA at the last period

        # Representing the trends
        self.UP = 1
        self.sUP = 2
        self.FLAT = 3
        self.sDOWN = 4
        self.DOWN = 5
        Log("peroid: %d; ma: long %d, short %d; buy ratio %f" %(self.period, self.ma_long, self.ma_short, self.buy_ratio))

    def get_current_ma_trend(self, s_ma, l_ma):
        # Trend determination method: MA Cross
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None

        Log("s_ma %f l_ma %f" %(s_ma, l_ma))
        if s_ma > l_ma:
            return self.UP
        elif s_ma < l_ma:
            return self.DOWN
        return self.FLAT
    
    def granville(self, close_price, s_ma, ma_trend):
        # Currently implemented: rules 1 and 5
        if np.isnan(close_price) or np.isnan(s_ma) or ma_trend == None:
            return -1

        # Log("cur price %f ma %f; last price %f ma %f" %(close_price, ma, self.close_price_trace[-2], self.last_ma))
        if ma_trend == self.UP:
            if self.close_price_trace[-2] < self.last_s_ma and close_price > s_ma:
                return 1
        if ma_trend == self.DOWN:
            if self.close_price_trace[-2] > self.last_s_ma and close_price < s_ma:
                return 5
        return 0

    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        cur_ma_trend = self.get_current_ma_trend(s_ma, l_ma)
        if cur_ma_trend is None:
            return []
        cur_type = self.granville(float(close_price),s_ma, cur_ma_trend)
        # if cur_type > 0:
        #     Log("current trend: %d" %cur_type)
        self.last_s_ma = s_ma
        # Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['BTC']))

        if self.last_ma_trend is None:
            self.last_ma_trend = cur_ma_trend
            return []
        self.last_ma_trend = cur_ma_trend
        
        action = 'wait'        
        if self.last_type == 'sell' and cur_type > 0 and cur_type <= 4:
            action = 'buy' # Rules 1 to 4 => buy
        elif self.last_type == 'buy' and cur_type > 4:
            action = 'sell' # Rules 5 to 8 => sell

        if action == 'buy':
            # Log('buying, ' + exchange + ':' + pair)
            self.last_type = 'buy'
            self.last_buy = float(close_price)
            return [
                {
                    'exchange': exchange,
                    'amount': self['assets'][exchange]['USDT'] * self.buy_ratio / float(close_price),
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif action == 'sell':
            # Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_buy = -1
            return [
                {
                    'exchange': exchange,
                    'amount': -self['assets'][exchange]['BTC'],
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        return [] # Default case 'wait'
