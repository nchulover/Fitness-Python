import sqlite3

import pandas as pd

from bmob_beans import HeatRecord

DATA_BASE_NAME = 'database.db'


def update_db(data_frame):
    connection = sqlite3.connect(DATA_BASE_NAME)
    cursor = connection.cursor()

    for index, row in data_frame.iterrows():
        user_id = row['user']
        heat_change = row['heatChange']
        time = row['time']
        m_type = row['type']
        cursor.execute(
            "INSERT INTO HeatRecord (userId, heatChange, time, type)" +
            "VALUES (?,?,?,?);", (user_id, heat_change, time, m_type)
        )

    connection.commit()
    connection.close()


def query_data(user_id):
    connection = sqlite3.connect(DATA_BASE_NAME)

    cursor = connection.cursor()
    cursor.execute("SELECT * from HeatRecord WHERE userId = ?", [user_id])
    result = cursor.fetchall()

    connection.close()

    heat_record_list = []
    for item_tuple in result:
        dict = {
            'user': {
                'objectId': item_tuple[1]
            },
            'heatChange': item_tuple[2],
            'time': {
                'iso': item_tuple[3]
            },
            'type': item_tuple[4]
        }
        heat_record_list.append(HeatRecord(dict))
    return heat_record_list


if __name__ == '__main__':
    database = sqlite3.connect("database.db")
    cursor = database.cursor()
    cursor.execute(
        "DROP TABLE IF EXISTS HeatRecord"
    )
    cursor.execute(
        "CREATE TABLE HeatRecord (" +
        "id INTEGER PRIMARY KEY NOT NULL," +
        "userId TEXT NOT NULL," +
        "heatChange REAL NOT NULL," +
        "time DATETIME NOT NULL," +
        "type INTEGER NOT NULL" +
        ")"
    )

    df = pd.DataFrame(pd.read_csv('heat_record.csv'))
    update_db(df)
    result_list = query_data('0f1d4db0bf')
    for heat_record in result_list:
        print(heat_record.user_id, heat_record.heat_change, heat_record.type, heat_record.time, sep=',')
