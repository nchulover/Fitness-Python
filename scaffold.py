import datetime

import dateutil
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

import database
from bmob import Bmob, BmobQuerier, BmobPointer
from bmob_beans import PhysicalStatistic, Sport, HeatRecord
import matplotlib.pyplot as plt
import arima.pre_interface as pre

bmob = Bmob()


class BodyToleranceCalculator:
    """
        取用数据：
        BodyToleranceCalculator.body_tolerance<int>
    """

    def __init__(self, user):
        self.user_id = user.object_id
        self.gender = user.gender
        self.statistic = None
        self.bmi = None
        self.vcwi = None
        self.body_tolerance = None
        # 0男1女
        self.vcwi_table = [
            [47, 49, 51, 52, 54, 55, 58, 61, 64, 66, 68, 71, 73, 75, 77, 78, 80, 81, 82, 83, 84],
            [35, 37, 39, 41, 42, 43, 46, 49, 51, 53, 54, 57, 59, 61, 63, 64, 65, 67, 68, 69, 70]
        ]
        self.bmi_table = [
            40, 30, 27, 24, 18.5
        ]

    def work(self):
        self.statistic = self.__get_statistic__(self.user_id)
        self.bmi = self.__calculate_bmi__(self.statistic)
        self.vcwi = self.__calculate_vital_capacity_and_weight_index__(self.statistic)
        self.body_tolerance = self.__evaluate_body_tolerance__()

    @staticmethod
    def __get_statistic__(user_id):
        result = bmob.find('_User',
                           BmobQuerier().
                           addWhereEqualTo('objectId', user_id)
                           )
        result = result.jsonData.get('results')
        if len(result) != 1:
            return None
        latest_statistic_id = result[0].get('latestStatistic').get('objectId')
        result = bmob.find('PhysicalStatistic',
                           BmobQuerier().
                           addWhereEqualTo('objectId', latest_statistic_id)
                           )
        result = result.jsonData.get(u'results')
        if len(result) != 1:
            return None
        statistic = PhysicalStatistic(result[0])
        return statistic

    @staticmethod
    def __calculate_bmi__(statistic):
        return statistic.weight / pow((statistic.height / 100), 2)

    @staticmethod
    def __calculate_vital_capacity_and_weight_index__(statistic):
        return statistic.vital_capacity / statistic.weight

    @staticmethod
    def __get_vcwi_level__(vcwi_table, user_vcwi, user_gender):
        """
        :param vcwi_table:
        :param user_vcmi:
        :param user_gender:
        :return: [1, 10]范围内的浮点值
        """
        vcwi_gender_table = vcwi_table[user_gender]

        judged = False
        level_index = 0
        if user_vcwi <= vcwi_gender_table[0]:
            level_index = 0
            judged = True
        elif user_vcwi >= vcwi_gender_table[len(vcwi_gender_table) - 1]:
            level_index = len(vcwi_gender_table)
            judged = True

        if not judged:
            for i in range(0, len(vcwi_gender_table) - 2):
                left = vcwi_gender_table[i]
                right = vcwi_gender_table[i + 1]
                if left <= user_vcwi <= right:
                    level_index = i + 1
        # 将[0, len] -> [1, 10]
        # y = 9/len * x + 1
        real_level = level_index * 9 / len(vcwi_gender_table) + 1
        return real_level

    @staticmethod
    def __get_bmi_level__(bmi_table, user_bmi):
        """
        :return: [1, 10]范围内的浮点值
        """
        judged = False
        level_index = 0
        if user_bmi >= bmi_table[0]:
            level_index = 0
            judged = True
        elif user_bmi <= bmi_table[len(bmi_table) - 1]:
            level_index = len(bmi_table)
            judged = True

        if not judged:
            for i in range(0, len(bmi_table) - 2):
                left = bmi_table[i]
                right = bmi_table[i + 1]
                if left >= bmi_table >= right:
                    level_index = i + 1
        # 将[0, len] -> [5, 10]
        # y = 5/len * x + 1
        real_level = level_index * 5 / len(bmi_table) + 1
        return real_level

    def __evaluate_body_tolerance__(self):
        """
        :return: [1, 10]范围内的整数
        """
        vcwi_level = self.__get_vcwi_level__(self.vcwi_table, self.vcwi, self.gender)
        bmi_level = self.__get_bmi_level__(self.bmi_table, self.bmi)
        return int((vcwi_level + bmi_level) / 2)


class AvailableSportGetter:
    """
        取用数据：
        AvailableSportGetter.available_sport_list<bmob_beans.Sport[]>
    """

    def __init__(self, user):
        self.tolerance_calculator = BodyToleranceCalculator(user)
        self.available_sport_list = None

    def work(self):
        self.tolerance_calculator.work()
        self.available_sport_list = self.__get_available_sport__(
            self.tolerance_calculator.body_tolerance
        )

    # TODO 每次都是远程拉取，应改成本地缓存一份文件， 都直接用这份文件读取，按照标记进行更新
    @staticmethod
    def __get_available_sport__(user_body_tolerance):
        """
        :param user_body_tolerance:
        :return: 可承受的运动列表
        """
        result = bmob.find('Sport',
                           BmobQuerier()
                           .addWhereLessThanOrEqualTo('difficulty', user_body_tolerance)
                           )
        sport_list = result.jsonData.get('results')
        available_list = []
        for sport_json in sport_list:
            available_list.append(Sport(sport_json))

        return available_list


class HeatIncome:
    def __init__(self, heat_change, date):
        self.heat_change = heat_change
        self.date = date


class UserHeatRecordGetter:
    """
        数据取用：
        UserHeatRecordGetter.heat_record_list<bmob_beans.HeatRecord[]>
        UserHeatRecordGetter.income_heat_record_list<HeatIncome[]>
    """

    def __init__(self, user):
        self.user_id = user.object_id
        self.heat_record_list = None
        self.income_heat_record_list = None

    def work(self):
        self.heat_record_list = self.__get_user_heat_record_locally__(self.user_id)
        self.income_heat_record_list = self.__get_income_heat_record_list__(self.heat_record_list)

    @staticmethod
    def __get_user_heat_record_locally__(user_id):
        """
        :param user_id:
        :return: HeatRecord[]
        """
        return database.query_data(user_id)

    @staticmethod
    def __get_income_heat_record_list__(heat_record_list):
        income_heat_record_list = []
        i = 0
        while i <= len(heat_record_list) - 1:
            today_income = 0
            today = heat_record_list[i].time
            visited = 0
            for j in range(i, len(heat_record_list)):
                temp = heat_record_list[j]
                visited += 1
                if temp.time.date().__eq__(today):
                    if temp.type is not 4 and temp.heat_change >= 0:
                        today_income += temp.heat_change
                else:
                    visited -= 1
                    break
            i += visited
            income_heat_record_list.append(HeatIncome(today_income, today))
        return income_heat_record_list


class HeatIncomeModel:

    def __init__(self, user):
        self.user_id = user.object_id
        heat_record_getter = UserHeatRecordGetter(user)
        heat_record_getter.work()
        self.income_heat_record_list = heat_record_getter.income_heat_record_list

    @staticmethod
    def __draw_ts__(time_series):
        time_series.plot()
        plt.show()

    @staticmethod
    def __get_time_series__(heat_income_time_list, heat_income_value_list):
        full_data_data_frame = pd.DataFrame({
            'date': heat_income_time_list,
            'heat_change': heat_income_value_list
        })
        full_data_data_frame = full_data_data_frame.set_index('date')
        full_data_data_frame.index = pd.to_datetime(full_data_data_frame.index)
        return full_data_data_frame['heat_change']

    def predict(self, predict_target_date):
        heat_income_time_list = []
        heat_income_value_list = []
        for heat_income in self.income_heat_record_list:
            date = heat_income.date
            heat_income_time_list.append(str(datetime.datetime(date.year, date.month, date.day)))
            heat_income_value_list.append(heat_income.heat_change)
        # 获取组装好的时间序列
        full_data_time_series = self.__get_time_series__(heat_income_time_list, heat_income_value_list)
        # self.__draw_ts__(full_data_time_series)

        last_date = dateutil.parser.parse(heat_income_time_list[len(heat_income_time_list) - 1])
        date_after = (predict_target_date - last_date).days
        if date_after < 1:
            print('argument wrong!')
            date_after = 1

        # predict_result_list = self.__predict_arima__(heat_income_value_list, date_after)
        predict_result = self.__predict_linear_regression__(heat_income_value_list, date_after)

        # 拼接预测
        # for predict_result in predict_result_list:
        #     last_date += datetime.timedelta(days=1)
        #     heat_income_time_list.append(str(last_date))
        #     heat_income_value_list.append(predict_result)
        # full_data_time_series = self.__get_time_series__(heat_income_time_list, heat_income_value_list)
        # self.__draw_ts__(full_data_time_series)

        # return predict_result_list[date_after - 1]
        return predict_result

    @staticmethod
    def __predict_arima__(heat_income_value_list, date_after):
        return pre.predict(heat_income_value_list, date_after)

    @staticmethod
    def __predict_linear_regression__(heat_income_value_list, date_after):
        model = LinearRegression()
        X = []
        Y = []
        for i in range(len(heat_income_value_list)):
            X.append([i])
            Y.append([heat_income_value_list[i]])
        last_index = len(X) - 1
        model.fit(X, Y)
        pre_x = [[last_index + date_after]]
        return model.predict(pre_x)


class NetHeatCalculator:

    def __init__(self):
        pass

    @staticmethod
    def work(predict_income, weight):
        return predict_income - weight * 22


class ExerciseTask:
    def __init__(self, sport, time):
        self.sport = sport
        self.time = time

    def to_string(self):
        return 'sport=[' + self.sport.sport_name + '], time=[' + str(self.time) + ' h]'


class MultiExerciseTask:
    def __init__(self, task_list):
        self.task_list = task_list

    def to_string(self):
        string = ''
        for task in self.task_list:
            string += task.to_string() + ', '
        return string


class ExerciseTaskMaker:

    def __init__(self, user, statistic, date):
        self.user = user
        worker = AvailableSportGetter(user)
        worker.work()
        self.available_sport_list = worker.available_sport_list
        self.predict_income = HeatIncomeModel(user).predict(date)
        self.net_heat = NetHeatCalculator.work(self.predict_income, statistic.weight)
        self.available_sport_exercise_time_list = None
        self.exercise_task_list = None
        self.multi_exercise_task_list = None

    def work(self):
        self.exercise_task_list = []
        self.available_sport_exercise_time_list = self.__get_exercise_time__(self.available_sport_list, self.net_heat)
        for i in range(len(self.available_sport_exercise_time_list) - 1):
            sport = self.available_sport_list[i]
            time = self.available_sport_exercise_time_list[i]
            self.exercise_task_list.append(ExerciseTask(sport, time))
        self.multi_exercise_task_list = []

        m_list = []
        for elem in self.available_sport_list:
            m_list.append(elem)
        np.random.shuffle(m_list)
        i = 0
        while i < len(m_list) - 3:
            multi_task_list = []
            task = self.exercise_task_list[i]
            multi_task_list.append(ExerciseTask(task.sport, task.time / 3))
            task = self.exercise_task_list[i + 1]
            multi_task_list.append(ExerciseTask(task.sport, task.time / 3))
            task = self.exercise_task_list[i + 2]
            multi_task_list.append(ExerciseTask(task.sport, task.time / 3))
            self.multi_exercise_task_list.append(MultiExerciseTask(multi_task_list))
            i += 3

    @staticmethod
    def __get_exercise_time__(sport_list, heat_target):
        exercise_time_list = []
        for sport in sport_list:
            exercise_time = heat_target / sport.calories_per_unit
            exercise_time_list.append(exercise_time)
        return exercise_time_list
