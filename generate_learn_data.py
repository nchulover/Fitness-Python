import numpy as np
import pandas as pd


def get_sport_level(bmi, target_heat_change):
    point = 5  # 应该在1-10
    if bmi < 18.5:
        point -= 2
    elif 25 < bmi < 30:
        point -= 1
    elif bmi < 50:
        point -= (bmi - 30) % 5
    else:
        point = 0

    if target_heat_change > 0:
        point = 2
    else:
        point += abs(target_heat_change) / 200

    return int(point)


bmi_list = []
target_heat_change_list = []
sport_level_list = []
for index in range(0, 1000):
    # 10 - 60
    bmi = 50 * np.random.random() + 10
    # -1000 - 1000
    target_heat_change = 2000 * np.random.random() - 1000

    sport_level = get_sport_level(bmi, target_heat_change)

    bmi_list.append(bmi)
    target_heat_change_list.append(target_heat_change)
    sport_level_list.append(sport_level)
data = {'bmi': bmi_list, 'targetCalories': target_heat_change_list, 'sportLevel': sport_level_list}
df = pd.DataFrame(data)
df.to_csv(r'./TrainingData.csv', columns=['bmi', 'targetCalories', 'sportLevel'], index=False,
          sep=',')
