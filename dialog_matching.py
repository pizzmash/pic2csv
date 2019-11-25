import csv
import cv2
import numpy as np


def read_csv(path):
    fp = open(path, 'r', newline='')
    return csv.DictReader(fp)


def culc_overlap(rect1, rect2):
    sx = max([rect1[0], rect2[0]])
    sy = max([rect1[1], rect2[1]])
    ex = min([rect1[0]+rect1[2], rect2[0]+rect2[2]])
    ey = min([rect1[1]+rect1[3], rect2[1]+rect2[3]])

    w = ex - sx
    h = ey - sy

    if w > 0 and h > 0:
        return [sx, sy, w, h]
    else:
        return None


def culc_area(rect):
    return rect[2] * rect[3]


def culc_F(frame, frame_ref):
    overlap = culc_overlap(frame, frame_ref)
    if overlap is None:
        return 0
    else:
        area_m = culc_area(frame)
        area_r = culc_area(frame_ref)
        area_o = culc_area(overlap)

        recall = area_o / area_r
        precision = area_o / area_m
        return 2 / ((1/recall) + (1/precision))


def recall_matching(frames, frames_ref):
    matched_Fs = []
    matched_indexes = []
    for rframe in frames_ref:
        Fs = [culc_F(frame, rframe) for frame in frames]
        max_F = max(Fs)
        max_index = Fs.index(max_F)
        matched_Fs.append(max_F if max_F != 0 else None)
        matched_indexes.append(max_index if max_F != 0 else None)

    # 重複フレームを一つに絞る
    dup_values = [v for v in set(matched_indexes) if v is not None and matched_indexes.count(v) > 1]
    for dv in dup_values:
        dup_indexes = [di for di, v in enumerate(matched_indexes) if v == dv]
        Fs = [matched_Fs[di] for di in dup_indexes]
        max_index = Fs.index(max(Fs))
        for i, di in enumerate(dup_indexes):
            if i != max_index:
                matched_indexes[di] = None

    return matched_indexes


def rectangles(img, frames, color, thickness=1):
    for frame in frames:
        cv2.rectangle(
            img,
            (frame[0], frame[1]),
            (frame[0]+frame[2], frame[1]+frame[3]),
            color,
            thickness=thickness
        )


def draw_frames(img, frames, frames_ref):
    rectangles(img, frames, (0, 255, 0))
    rectangles(img, frames_ref, (255, 0, 0))


def draw_recall_matched_frames(img, frames, frames_ref):
    matched = recall_matching(frames, frames_ref)
    for i, j in enumerate(matched):
        if j is None:
            continue
        else:
            color = tuple([int(r) for r in np.random.randint(0, 256, 3)])
            rectangles(img, [frames[j], frames_ref[i]], color, thickness=3)


def extract_frame_info(frame):
    info_names = ['startX', 'startY', 'width', 'height']
    return [int(frame[name]) for name in info_names]


def main():
    pages = read_csv('pages.csv')
    pages_ref = read_csv('pages_ref.csv')
    for page, rpage in zip(pages, pages_ref):
        frames = read_csv('frames.csv')
        frames_ref = read_csv('frames_ref.csv')
        img = cv2.imread(page['source'], cv2.IMREAD_COLOR)
        frames = [extract_frame_info(frame) for frame in frames if frame['page_id'] == page['page_id']]
        rframes = [extract_frame_info(rframe) for rframe in frames_ref if rframe['page_id'] == page['page_id']]
        draw_frames(img, frames, rframes)
        draw_recall_matched_frames(img, frames, rframes)
        cv2.imshow('matched', img)
        cv2.waitKey(0)



if __name__ == '__main__':
    main()
