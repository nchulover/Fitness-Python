import datetime
import numpy as np
import pandas as pd
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose


class ModelDecomposition:
    def __init__(self, time_series):
        self.ts = time_series
        self.test_size = len(self.ts) // 7
        self.train_size = len(self.ts) - self.test_size
        self.train = self.ts[:len(self.ts) - self.test_size]
        self.test = self.ts[-self.test_size:]

    @staticmethod
    def diff_smooth(ts):
        dif = ts.diff().dropna()  # 差分序列
        td = dif.describe()  # 描述性统计得到：min，25%，50%，75%，max值
        high = td['75%'] + 1.5 * (td['75%'] - td['25%'])  # 定义高点阈值，1.5倍四分位距之外
        low = td['25%'] - 1.5 * (td['75%'] - td['25%'])  # 定义低点阈值，同上

        # 变化幅度超过阈值的点的索引
        forbid_index = dif[(dif > high) | (dif < low)].index
        i = 0
        while i < len(forbid_index) - 1:
            n = 1  # 发现连续多少个点变化幅度过大，大部分只有单个点
            start = forbid_index[i]  # 异常点的起始索引
            while forbid_index[i + n] == start + datetime.timedelta(minutes=n):
                n += 1
            i += n - 1

            end = forbid_index[i]  # 异常点的结束索引
            # 用前后值的中间值均匀填充
            value = np.linspace(ts[start - datetime.timedelta(minutes=1)],
                                ts[end + datetime.timedelta(minutes=1)], n)
            ts[start: end] = value
            i += 1

    def decompose(self, freq):
        decomposition = seasonal_decompose(self.ts, freq=freq, two_sided=False)
        self.trend = decomposition.trend
        self.seasonal = decomposition.seasonal
        self.residual = decomposition.resid
        self.decomposition = decomposition

    def trend_model(self, order):
        self.trend.dropna(inplace=True)
        train = self.trend[:len(self.trend) - self.test_size]
        # arima的训练参数order =（p,d,q），具体意义查看官方文档，调参过程略。
        self.trend_model = ARIMA(train, order).fit(disp=-1, method='css')
        d = self.residual.describe()
        delta = d['75%'] - d['25%']
        self.low_error, self.high_error = (d['25%'] - 1 * delta, d['75%'] + 1 * delta)

    def predict_new(self, time_iso_list):
        '''
        预测新数据
        '''
        # 续接train，生成长度为n的时间索引，赋给预测序列
        n = self.test_size
        self.pred_time_index = pd.DatetimeIndex(
            time_iso_list, dtype='datetime64[ns]')
        self.trend_pred = self.trend_model.forecast(n)[0]
        self.add_season()
        return self.final_pred, self.low_conf, self.high_conf

    def add_season(self):
        '''
        为预测出的趋势数据添加周期数据和残差数据
        '''
        self.train_season = self.seasonal[:self.train_size]
        values = []
        low_conf_values = []
        high_conf_values = []

        for i, t in enumerate(self.pred_time_index):
            trend_part = self.trend_pred[i]

            # 相同时间点的周期数据均值
            season_part = self.train_season[
                self.train_season.index.time == t.time()
                ].mean()

            # 趋势 + 周期 + 误差界限
            predict = trend_part + season_part
            low_bound = trend_part + season_part + self.low_error
            high_bound = trend_part + season_part + self.high_error

            values.append(predict)
            low_conf_values.append(low_bound)
            high_conf_values.append(high_bound)

        # 得到预测值，误差上界和下界
        self.final_pred = pd.Series(values, index=self.pred_time_index, name='predict')
        self.low_conf = pd.Series(low_conf_values, index=self.pred_time_index, name='low_conf')
        self.high_conf = pd.Series(high_conf_values, index=self.pred_time_index, name='high_conf')
