# coding=utf-8
import pandas as pd
import numpy as np

from bmob import *
from sklearn.linear_model import LinearRegression

b = Bmob("553bcebf8a76c1b58994160184ee8324", "be5915bfc82009fa0ea49038c7b740b6")


def get_target_sport_id(target_user_object_id):
    # 查询他的最近身体信息
    result = b.find('_User',
                    BmobQuerier().
                    addWhereEqualTo('objectId', target_user_object_id)
                    )
    dict_array = result.jsonData.get(u'results')
    # 查询到的数据应只有1个，或者失败为0个
    if len(dict_array) != 1:
        # 失败了，结束
        return

    user_info_json = dict_array[0]
    latest_physical_statistic_id = user_info_json.get('latestStatistic').get('objectId')
    result = b.find('PhysicalStatistic',
                    BmobQuerier().
                    addWhereEqualTo('objectId', latest_physical_statistic_id)
                    )
    dict_array = result.jsonData.get(u'results')
    # 查询到的数据应只有1个，或者失败为0个
    if len(dict_array) != 1:
        # 失败了，结束
        return
    physical_statistic_json = dict_array[0]

    height_in_cm = physical_statistic_json.get('height')
    weight_in_kg = physical_statistic_json.get('weight')
    bmi = weight_in_kg / (height_in_cm / 100) / (height_in_cm / 100)
    # 开始拿热量记录
    result = b.find('HeatRecord',
                    BmobQuerier().
                    addWhereEqualTo('user', target_user_object_id)
                    )
    dict_array = result.jsonData.get(u'results')
    if len(dict_array) == 0:
        return

    # 生成机器学习所需的X，Y
    index = -1
    indexes = []
    heat_change = []
    for lineJson in dict_array:
        index += 1
        indexes.append([index])
        heat_change.append([lineJson.get(u'heatChange')])

    model = LinearRegression()
    model.fit(indexes, heat_change)
    predict_heat_change = model.predict([[index + 1]])
    target_calories = -predict_heat_change[0][0]

    # 查询大概符合热量变化的运动
    result = b.find('Sport',
                    order='-calories'
                    )
    dict_array = result.jsonData.get(u'results')
    target_sport_object_id = None
    available_sports = []
    for lineJson in dict_array:
        if float(lineJson.get(u'calories')) < -target_calories:
            available_sports.append(lineJson)
    if len(available_sports) > 0:
        target_sport_object_id = available_sports[0].get(u'objectId')

    return target_sport_object_id


while True:
    mails = b.find('ClientMailbox',
                   BmobQuerier().
                   addWhereEqualTo('valid', True).
                   addWhereEqualTo('type', 1))
    dict_arr = mails.jsonData.get(u'results')
    print('Working!')
    if dict_arr is not None:
        for line_json in dict_arr:
            mail_id = line_json.get('objectId')
            user_id = line_json.get(u'user').get('objectId')
            target_sport_id = get_target_sport_id(user_id)
            if target_sport_id is not None:
                data_dic = {
                    'valid': True,
                    'obj': '{"sportId":"' + target_sport_id + '"}',
                    'user': BmobPointer('_User', user_id),
                    'clientMail': BmobPointer('ClientMailbox', mail_id)
                }
                print(data_dic)
                b.insert(
                    'ServerMailbox',
                    data_dic
                )
            else:
                print('Unknown error!')
            b.update('ClientMailbox', mail_id,
                     {'valid': False}
                     )
    else:
        print('Unknown error!')
