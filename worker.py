import datetime

from bmob import Bmob, BmobQuerier, BmobPointer
from bmob_beans import FitnessUser, PhysicalStatistic
from scaffold import ExerciseTaskMaker

bmob = Bmob()

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

        maker = ExerciseTaskMaker(user, statistic, datetime.date.today() + datetime.timedelta(days=0))
        maker.work()
        multi_sport_task_list = maker.multi_exercise_task_list
        for multi_sport_task in multi_sport_task_list:
            sport1 = multi_sport_task.task_list[0].sport
            sport2 = multi_sport_task.task_list[1].sport
            sport3 = multi_sport_task.task_list[2].sport
            time1 = multi_sport_task.task_list[0].time
            time2 = multi_sport_task.task_list[1].time
            time3 = multi_sport_task.task_list[2].time
            data_dic = {
                'targetUser': BmobPointer('_User', '0f1d4db0bf'),
                'data': '{"sportList":[\"' + sport1.object_id + '\",\"' + sport2.object_id + '\",\"' + sport3.object_id + '\"],"timeList":[' + str(int(time1 * 60)) + ',' + str(
                    int(time2 * 60)) + ',' + str(
                    int(time1 * 60)) + ']}'
            }
            print(data_dic)
            # bmob.insert('SportRecommend', data_dic)
            # bmob.insert('ExerciseTask', data_dic)
            # print('insert success!')
