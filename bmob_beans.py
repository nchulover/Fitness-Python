import datetime


class FitnessUser:

    def __init__(self, json):
        self.object_id = json.get('objectId')
        self.gender = int(json.get('gender'))
        birthday = datetime.datetime.fromisoformat(json.get('birthday').get('iso'))
        self.age = self.__calculate_age(birthday.date())
        self.physical_statistic_id = json.get('latestStatistic').get('objectId')

    @staticmethod
    def __calculate_age(born):
        today = datetime.date.today()
        try:
            birthday = born.replace(year=today.year)
        # raised when birth date is February 29 and the current year is not a leap year
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month + 1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year


class Sport:

    def __init__(self, json):
        self.object_id = json.get('objectId')
        self.sport_name = json.get('sportName')
        self.calories_per_unit = float(json.get('caloriesPerUnit'))
        self.difficulty = int(json.get('difficulty'))


class PhysicalStatistic:

    def __init__(self, json):
        self.object_id = json.get('objectId')
        self.height = float(json.get('height'))
        self.weight = float(json.get('weight'))
        self.heart_rate = float(json.get('heartRate'))
        self.vital_capacity = float(json.get('vitalCapacity'))


class HeatRecord:

    def __init__(self, json):
        self.object_id = json.get('objectId')
        self.heat_change = float(json.get('heatChange'))
        self.user_id = json.get('user').get('objectId')
        self.time = datetime.datetime.fromisoformat(json.get('time').get('iso'))
        # 1早餐2午餐3晚餐4运动消耗, 0不正常数值
        self.type = json.get('type')
