from build import recognize_captcha
import csv
import cv2
import os
import json
from itertools import zip_longest


source_uri = '/Users/pizzmash/Documents/work/cylog/resource/ブラックジャックによろしく5'


def read_csv(path):
    f = open(path, 'r', newline='')
    data = csv.DictReader(f)
    return data


def trim(frames_dict):
    frames = []
    pre_page_id = -1
    cnt = 0
    for fd in frames_dict:
        page_id = fd["page_id"]
        if page_id != pre_page_id:
            img = cv2.imread(os.path.join(source_uri, fd["source"]))
            if img is None:
                print('failed to read image')
                exit(-1)
            pre_page_id = page_id
        start_x = int(float(fd['t_startX']))
        start_y = int(float(fd['t_startY']))
        width = int(float(fd['t_width']))
        height = int(float(fd['t_height']))
        frames.append(img[
            start_y: start_y + height,
            start_x: start_x + width
        ])
        cnt += 1
        if cnt > 10:
            break
    return frames


def write_csv(path, origin, texts):
    with open(path, 'w', newline='') as f:
        texts_csv = csv.DictWriter(f, fieldnames=origin.fieldnames+['text'])
        texts_csv.writeheader()
        for row_origin, text in zip_longest(origin, texts):
            row = {k: v for k, v in row_origin.items()}
            row['text'] = text if text is not None else ''
            texts_csv.writerow(row)


if __name__ == "__main__":
    path = '/Users/pizzmash/Documents/work/cylog/resource/ブラックジャックによろしく5/frames.csv'
    frames_dict = read_csv(path)

    """
    frames_dict = [
        {
            'page_id': 0,
            'source': '05bj_003.jpeg',
            't_startX': 240,
            't_startY': 1664,
            't_width': 170,
            't_height': 250,
        },
        {
            'page_id': 0,
            'source': '05bj_003.jpeg',
            't_startX': 1048,
            't_startY': 1588,
            't_width': 170,
            't_height': 250,
        },
    ]
    """

    frames = trim(frames_dict)

    # reload frames.csv
    frames_dict = read_csv(path)

    data = []
    for frame in frames:
        res = json.loads(recognize_captcha([frame]))['responses']
        data.append(res)

    # data = json.loads(recognize_captcha(frames))['responses']
    texts = []
    for d in data:
        key = "textAnnotations"
        if key in d[0]:
            texts.append(d[0][key][0]["description"])
        else:
            texts.append("")
    write_csv(
        '/Users/pizzmash/Documents/work/cylog/resource/ブラックジャックによろしく5/texts.csv',
        frames_dict,
        texts
    )
