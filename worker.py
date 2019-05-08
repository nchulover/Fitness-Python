import datetime

from bmob import Bmob, BmobQuerier, BmobPointer, BmobDate
from bmob_beans import FitnessUser, PhysicalStatistic
from scaffold import ExerciseTaskMaker

bmob = Bmob()


def __get_task_dic__(multi_sport_task):
    temp_dic = __get_recommend_dic__(multi_sport_task)
    temp_dic['time'] = BmobDate(datetime.date.today() + datetime.timedelta(days=1))
    return temp_dic


def __get_recommend_dic__(multi_sport_task):
    sport1 = multi_sport_task.task_list[0].sport
    sport2 = multi_sport_task.task_list[1].sport
    sport3 = multi_sport_task.task_list[2].sport
    time1 = multi_sport_task.task_list[0].time
    time2 = multi_sport_task.task_list[1].time
    time3 = multi_sport_task.task_list[2].time
    return {
        'targetUser': BmobPointer('_User', '0f1d4db0bf'),
        'data': '{"sportList":[\"' + sport1.object_id + '\",\"' + sport2.object_id + '\",\"' + sport3.object_id + '\"],"timeList":[' + str(int(time1 * 60)) + ',' + str(
            int(time2 * 60)) + ',' + str(
            int(time1 * 60)) + ']}'
    }


if __name__ == '__main__':
    result = bmob.find('_User').jsonData.get('results')
    user_list = []
    for json in result:
        user_list.append(FitnessUser(json))

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
        multi_sport_task_list = maker.multi_exercise_task_list
        if len(multi_sport_task_list) > 3:
            multi_sport_task_list = multi_sport_task_list[:3]
        for multi_sport_task in multi_sport_task_list:
            bmob.insert('ExerciseTask', __get_task_dic__(multi_sport_task))
        for recommend_sports in multi_sport_task_list:
            bmob.insert('SportRecommend', __get_recommend_dic__(recommend_sports))
