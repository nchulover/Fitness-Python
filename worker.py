import datetime

from numpy import random

from bmob import Bmob, BmobQuerier, BmobPointer, BmobDate
from bmob_beans import FitnessUser, PhysicalStatistic, Meal
from scaffold import ExerciseTaskMaker

bmob = Bmob()


def __get_exercise_task_dic__(user_id, multi_sport_task):
    temp_dic = __get_sport_recommend_dic__(user_id, multi_sport_task)
    temp_dic['time'] = BmobDate(datetime.date.today() + datetime.timedelta(days=1))
    return temp_dic


def __get_sport_recommend_dic__(user_id, multi_sport_task):
    sport1 = multi_sport_task.task_list[0].sport
    sport2 = multi_sport_task.task_list[1].sport
    sport3 = multi_sport_task.task_list[2].sport
    time1 = multi_sport_task.task_list[0].time
    time2 = multi_sport_task.task_list[1].time
    time3 = multi_sport_task.task_list[2].time
    return {
        'targetUser': BmobPointer('_User', user_id),
        'data': '{"sportList":[\"' + sport1.object_id + '\",\"' + sport2.object_id + '\",\"' + sport3.object_id + '\"],"timeList":[' + str(int(time1 * 60)) + ',' + str(
            int(time2 * 60)) + ',' + str(
            int(time1 * 60)) + ']}'
    }


def __get_meal_recommend_dic__(user_id, breakfast_meal_list, lunch_meal_list, dinner_meal_list):
    meal_id_list_string = '['
    for meal in breakfast_meal_list:
        meal_id_list_string = meal_id_list_string + '\"' + meal.meal_name + '\",'
    meal_id_list_string = meal_id_list_string[:-1] + ']'
    breakfast_meal_list_string = meal_id_list_string
    meal_id_list_string = '['
    for meal in lunch_meal_list:
        meal_id_list_string = meal_id_list_string + '\"' + meal.meal_name + '\",'
    meal_id_list_string = meal_id_list_string[:-1] + ']'
    lunch_meal_list_string = meal_id_list_string
    meal_id_list_string = '['
    for meal in dinner_meal_list:
        meal_id_list_string = meal_id_list_string + '\"' + meal.meal_name + '\",'
    meal_id_list_string = meal_id_list_string[:-1] + ']'
    dinner_meal_list_string = meal_id_list_string
    return {
        'targetUser': BmobPointer('_User', user_id),
        'time': BmobDate(datetime.date.today() + datetime.timedelta(days=1)),
        'data': '{"mealList":{"breakfast":' + breakfast_meal_list_string + ',"lunch":' + lunch_meal_list_string + ',"dinner":' + dinner_meal_list_string + '}}'
    }


def get_meal_list():
    result = bmob.find('Meal',
                       order='calories').jsonData.get('results')
    meal_list = []
    for json in result:
        meal_list.append(Meal(json))
    return meal_list


def calc_meal_list(meal_list, target_calories, type):
    copy_meal_list = []
    for meal in meal_list:
        if meal.type is type:
            copy_meal_list.append(meal)

    min = 0
    max = len(copy_meal_list) - 1
    sum_calories = 0
    recommend_meal_list = []
    while sum_calories <= target_calories:
        r_index = int(random.rand() * max + min)
        meal = copy_meal_list[r_index]
        sum_calories = sum_calories + meal.calories
        recommend_meal_list.append(meal)
    return recommend_meal_list


if __name__ == '__main__':

    result = bmob.find('_User').jsonData.get('results')
    user_list = []
    for json in result:
        user_list.append(FitnessUser(json))

    ordered_meal_list = get_meal_list()

    for user in user_list:
        result = bmob.find('PhysicalStatistic',
                           BmobQuerier().
                           addWhereEqualTo('objectId', user.physical_statistic_id)
                           ).jsonData.get('results')
        if len(result) > 0:
            statistic = PhysicalStatistic(result[0])
        else:
            continue

        maker = ExerciseTaskMaker(user, statistic, datetime.datetime.today() + datetime.timedelta(days=1))
        maker.work()
        # Sports
        multi_sport_task_list = maker.multi_exercise_task_list
        if len(multi_sport_task_list) > 3:
            multi_sport_task_list = multi_sport_task_list[:3]
        for multi_sport_task in multi_sport_task_list:
            bmob.insert('ExerciseTask', __get_exercise_task_dic__(user.object_id, multi_sport_task))
        for recommend_sports in multi_sport_task_list:
            bmob.insert('SportRecommend', __get_sport_recommend_dic__(user.object_id, recommend_sports))
        # Meals
        pre_income = maker.predict_income
        pre_breakfast_income = pre_income * 0.3
        pre_lunch_income = pre_income * 0.3
        pre_dinner_income = pre_income * 0.2
        bmob.insert('MealRecommend', __get_meal_recommend_dic__(user.object_id,
                                                                calc_meal_list(ordered_meal_list, pre_breakfast_income, 1),
                                                                calc_meal_list(ordered_meal_list, pre_lunch_income, 0),
                                                                calc_meal_list(ordered_meal_list, pre_dinner_income, 1)
                                                                ))
