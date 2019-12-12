import csv
import cv2
import numpy as np
import Levenshtein
import matplotlib.pyplot as plt


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
        Fs = [culc_F(frame[0], rframe[0]) for frame in frames]
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
            (frame[0][0], frame[0][1]),
            (frame[0][0]+frame[0][2], frame[0][1]+frame[0][3]),
            color,
            thickness=thickness
        )


def draw_frames(img, frames, frames_ref):
    rectangles(img, frames, (0, 255, 0))
    rectangles(img, frames_ref, (255, 0, 0))


def draw_recall_matched_frames(img, frames, frames_ref, matched):
    for i, j in enumerate(matched):
        if j is None:
            continue
        else:
            color = tuple([int(r) for r in np.random.randint(0, 256, 3)])
            rectangles(img, [frames[j], frames_ref[i]], color, thickness=3)


def extract_frame_info(frame):
    dialog_names = ['startX', 'startY', 'width', 'height']
    text_names = 'text'
    return [[int(frame[name]) for name in dialog_names], frame[text_names]]


def remove_mini(frames, min_w=0, min_h=0):
    return [
        frame for frame in frames if frame[0][2] >= min_w and frame[0][3] >= min_h
    ]


def remove_inclusion(frames):
    remove_idx = []
    for i, fi in enumerate(frames):
        if i in remove_idx:
            continue
        for j, fj in enumerate(frames):
            if i != j:
                overlap = culc_overlap(fi[0], fj[0])
                if overlap is not None:
                    if overlap == fi[0]:
                        remove_idx.append(i)
                        break
                    elif overlap == fj[0]:
                        remove_idx.append(j)
    return [frame for i, frame in enumerate(frames) if i not in remove_idx]


def expand(frame, x_expansion, y_expansion):
    return [
        [
            max(0, frame[0][0]-x_expansion),
            max(0, frame[0][1]-y_expansion),
            frame[0][2]+x_expansion*2,
            frame[0][3]+y_expansion*2
        ],
        frame[1]
    ]


def create_graph(frames):
    graph = [[False] * len(frames) for _ in range(len(frames))]
    for i, fi in enumerate(frames):
        for j, fj in enumerate(frames):
            if i != j and culc_overlap(fi[0], fj[0]) is not None:
                graph[i][j] = True
                graph[j][i] = True
    return graph


def divide_groups(graph):
    def _divide_groups(idx, visited=None):
        visited = [idx] if visited is None else visited
        _groups = [idx]
        dest = [j for j, v in enumerate(graph[idx]) if v and j not in visited]
        for d in dest:
            _groups += _divide_groups(d, visited+dest)
        return _groups

    groups = []
    for i in range(len(graph)):
        if i not in [v for g in groups for v in g]:
            groups.append(_divide_groups(i))
    return groups


def sorted_by_distance(frames):
    return sorted(frames, key=lambda f: f[0][0]**2+f[0][1]**2, reverse=True)


def combine_nearby(frames, x_expansion=3, y_expansion=0):
    expanded = [expand(frame, x_expansion, y_expansion) for frame in frames]
    graph = create_graph(expanded)
    groups = divide_groups(graph)

    result = []
    for group in groups:
        gframes = [frames[i] for i in group]
        x = min([gf[0][0] for gf in gframes])
        y = min([gf[0][1] for gf in gframes])
        w = max([gf[0][0]+gf[0][2] for gf in gframes]) - x
        h = max([gf[0][1]+gf[0][3] for gf in gframes]) - y
        text = ''
        for gframe in sorted_by_distance(gframes):
            text += gframe[1]
        result.append([[x, y, w, h], text])
    return result


def preprocess(frames):
    result = remove_mini(frames, min_w=15, min_h=15)
    result = remove_inclusion(result)
    result = combine_nearby(result)
    return result


def main():
    pages = read_csv('pages.csv')
    pages_ref = read_csv('pages_ref.csv')
    n_frames = 0
    n_processed_frames = 0
    n_rframes = 0
    n_matched_frames = 0
    dists = []
    texts = []
    Fs = []
    for page_id, (page, rpage) in enumerate(zip(pages, pages_ref)):
        frames = read_csv('frames.csv')
        rframes = read_csv('frames_ref.csv')
        # img = cv2.imread(page['source'], cv2.IMREAD_COLOR)
        frames = [extract_frame_info(frame) for frame in frames if frame['page_id'] == page['page_id']]
        rframes = [extract_frame_info(rframe) for rframe in rframes if rframe['page_id'] == page['page_id']]
        # origin = frames
        n_frames += len(frames)
        n_rframes += len(rframes)
        frames = preprocess(frames)
        n_processed_frames += len(frames)
        # draw_frames(img, frames, rframes)
        matched = recall_matching(frames, rframes)
        # draw_recall_matched_frames(img, frames, rframes, matched)
        for i, m in enumerate(matched):
            str1 = frames[m][1].replace('\n', '') if m is not None else None
            str2 = rframes[i][1].replace('\n', '')
            if m is not None:
                dist = Levenshtein.distance(str1, str2)
                dist = float(dist) / max(len(str1), len(str2))
                dists.append(dist)
                texts.append((str1, str2))
                Fs.append(culc_F(frames[m][0], rframes[i][0]))
        n_matched_frames += sum([1 for m in matched if m is not None])
        # print()
        # rectangles(img, origin, (0, 0, 255))
        # cv2.imshow('result', img)
        # cv2.waitKey(0)
        # cv2.imwrite('../resource/ginga_preprocess/ginga_{}.png'.format(str(page_id+1).zfill(3)), img)
    n_matched_text = sum([1 for d in dists if d == 0])
    print('frames: {}'.format(n_frames))
    print('processed frames: {}'.format(n_processed_frames))
    print('reference frames: {}'.format(n_rframes))
    print('matched frames: {}'.format(n_matched_frames))
    print('distance average: {}'.format(sum(dists)/len(dists)))
    print('matched text: {} / {} = {}'.format(n_matched_text, n_matched_frames, n_matched_text/n_matched_frames))
    print('average F: {}'.format(sum(Fs)/len(Fs)))
    plt.hist(Fs)
    plt.show()
    plt.hist(dists)
    plt.show()
    """
    import random
    for v in range(10):
        idx = [i for i, d in enumerate(dists) if v*0.1 < d and d <= (v+1)*0.1]
        sample = random.sample(idx, 3)
        for s in sorted(sample, key=lambda x: dists[x]):
            print('systen: {}'.format(texts[s][0]))
            print('reference: {}'.format(texts[s][1]))
            print('distance: {}'.format(dists[s]))
            print()
    """


if __name__ == '__main__':
    main()
