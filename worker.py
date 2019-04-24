from bmob import Bmob, BmobQuerier, BmobPointer
from bmob_beans import FitnessUser, PhysicalStatistic
from scaffold import ExerciseTaskMaker

bmob = Bmob()

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
maker = ExerciseTaskMaker(user, statistic)
maker.work()
multi_sport_task_list = maker.multi_exercise_task_list
for multi_sport_task in multi_sport_task_list:
    print(multi_sport_task.to_string())
    sport1 = multi_sport_task.task_list[0].sport
    sport2 = multi_sport_task.task_list[1].sport
    sport3 = multi_sport_task.task_list[2].sport
    time1 = multi_sport_task.task_list[0].time
    time2 = multi_sport_task.task_list[1].time
    time3 = multi_sport_task.task_list[2].time
    data_dic = {
        'targetUser': BmobPointer('_User', '0f1d4db0bf'),
        'data': '{"sportList":[\"' + sport1.object_id + '\",\"' + sport2.object_id + '\",\"' + sport3.object_id + '\"],"timeList":[' + str(time1) + ',' + str(time2) + ',' + str(time3) + ']}'
    }
    bmob.insert('SportRecommend', data_dic)
    bmob.insert('ExerciseTask', data_dic)
    print('insert success!')
