import json
import csv

headers = ['location_type', 'location', 'wx1', 'wy1', 'wx2', 'wy2', 'rx1', 'ry1', 'rx2', 'ry2', 'similarity',
           'category']

location_type_int_map = {
    'null': 0,
    'absolute': 1,
    'relative': 2
}

sample = ['true widget', 'false widget']


def from_json_to_csv():
    d = json.load(open('/Users/pkun/PycharmProjects/ui_api_automated_test/decision_data/data_with_action_ui.json'))
    rows = []
    for index in d:
        descriptions = d[index]
        for desc in descriptions:
            data = descriptions[desc]
            for s in sample:
                row = [location_type_int_map[data['location type']]]
                if data['location type'] == 'null':
                    row.append(-1)
                    row.extend([0, 0, 0, 0, 0, 0, 0, 0])
                if data['location type'] == 'absolute':
                    row.append(data['grid int'])
                    row.extend(data[s]['bounds'])
                    row.extend([0, 0, 1080, 1920])
                if data['location type'] == 'relative':
                    row.append(data['relative int'])
                    row.extend(data[s]['bounds'])
                    row.extend(data['relative widget']['bounds'])
                similarity = round(data[s]['similarity'], 2)
                row.append(similarity)
                if 'true' in s:
                    row.append(1)
                else:
                    row.append(0)
                rows.append(row)
    with open('/Users/pkun/PycharmProjects/ui_api_automated_test/decision_data/origin_data.csv', 'w') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(rows)


if __name__ == '__main__':
    from_json_to_csv()
