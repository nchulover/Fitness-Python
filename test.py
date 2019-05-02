import datetime

import dateutil

from bmob import Bmob, BmobQuerier
from bmob_beans import FitnessUser, PhysicalStatistic
from scaffold import HeatIncomeModel, NetHeatCalculator

bmob = Bmob()

if __name__ == '__main__':
    result = bmob.find('_User',
                       BmobQuerier().
                       addWhereEqualTo('objectId', '0f1d4db0bf')
                       )
    user = FitnessUser(result.jsonData.get('results')[0])
    result = bmob.find('PhysicalStatistic',
                       BmobQuerier().
                       addWhereEqualTo('objectId', user.physical_statistic_id)
                       )
    statistic = PhysicalStatistic(result.jsonData.get('results')[0])
    worker = HeatIncomeModel(user)
    predict_result = worker.predict(dateutil.parser.parse('2019-04-25'))
    print(predict_result)
    result = NetHeatCalculator().work(predict_result, statistic.weight)
    print(result)
