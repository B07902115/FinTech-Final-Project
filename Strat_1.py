class Strategy():
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
        self.period = 20*60
        self.options = {}

        # User defined constants
        self.buy_ratio = 0.7                   # The ratio of the balance spent on buying BTC

        # user defined class attribute
        self.last_type = 'sell'                # Last action other than waiting
        self.last_cross_status = None          # Cross status of the last period
        self.close_price_trace = np.array([])  # The array of recent prices
        self.ma_short = 50                     # Range of coverage of the short MA, in periods
        self.ma_long = 300                     # Range of coverage of the long MA, in periods

        # Representing the trends
        self.UP = 1
        self.DOWN = 2
        Log("peroid: %d; long: %d; short: %d" %(self.period, self.ma_long, self.ma_short))


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        # Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['BTC']))

        if cur_cross is None:
            return []
        # Log('cross: ' + str(cur_cross))

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        action = 'wait'
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            action = 'buy'
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            action = 'sell'
        # cross up
        if action == 'buy':
            # Log('buying, ' + exchange + ':' + pair)
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.last_buy = close_price
            return [
                {
                    'exchange': exchange,
                    'amount': self['assets'][exchange]['USDT'] * self.buy_ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif action == 'sell':
            # Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
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
        self.last_cross_status = cur_cross
        return []