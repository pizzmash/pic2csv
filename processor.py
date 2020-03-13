import csv
import copy
from itertools import groupby
from enum import Enum


class PagesHeader(Enum):
    source = 'source'
    page_id = 'page_id'
    frames = 'frames'


class FramesHeader(Enum):
    source = 'source'
    page_id = 'page_id'
    frame_id = 'frame_id'
    start_x = 'startX'
    start_y = 'startY'
    width = 'width'
    height = 'height'
    text = 'text'


class Rectangle:
    def __init__(self, start_x, start_y, width, height):
        self.start_x = start_x
        self.start_y = start_y
        self.width = width
        self.height = height

    def expand(self, x_expansion, y_expansion):
        return Rectangle(
            start_x=max(0, self.start_x - x_expansion),
            start_y=max(0, self.start_y - y_expansion),
            width=self.width + x_expansion * 2,
            height=self.height + y_expansion * 2
        )

    def culc_overlapped_area(self, other):
        if not isinstance(other, Rectangle):
            return None
        sx = max([self.start_x, other.start_x])
        sy = max([self.start_y, other.start_y])
        ex = min([self.start_x+self.width, other.start_x+other.width])
        ey = min([self.start_y+self.height, other.start_y+other.height])
        w = ex - sx
        h = ey - sy
        if w > 0 and h > 0:
            return Rectangle(sx, sy, w, h)
        else:
            return None

    def __eq__(self, other):
        return isinstance(other, Rectangle) \
            and self.start_x == other.start_x \
            and self.start_y == other.start_y \
            and self.width == other.width \
            and self.height == other.height


class OverlapGraph:
    def __init__(self, rectangles):
        self.graph = [[False] * len(rectangles) for _ in range(len(rectangles))]
        for i, ri in enumerate(rectangles):
            for j, rj in enumerate(rectangles):
                if i != j and ri.culc_overlapped_area(rj) is not None:
                    self.graph[i][j] = True
                    self.graph[j][i] = True

    def divide_groups(self):
        def _divide_groups(idx, visited=None):
            visited = [idx] if visited is None else visited
            _groups = [idx]
            dest = [j for j, v in enumerate(self.graph[idx]) if v and j not in visited]
            for d in dest:
                _groups += _divide_groups(d, visited+dest)
            return _groups
        groups = []
        for i in range(len(self.graph)):
            if i not in [v for g in groups for v in g]:
                groups.append(_divide_groups(i))
        return groups


class PageBuffer:
    def __init__(self, source, page_id, frames):
        self.source = source
        self.page_id = page_id
        self.frames = frames

    def add_frame(frame):
        self.frames.append(frame)

    def remove_mini_frames(self, min_w, min_h):
        self.frames = [
            frame for frame in self.frames if frame.rectangle.width >= min_w and frame.rectangle.height >= min_h
        ]

    def remove_inclusion_frames(self):
        remove_idx = []
        for i, fi in enumerate(self.frames):
            if i in remove_idx:
                continue
            for j, fj in enumerate(self.frames):
                if i > j:
                    overlapped = fi.rectangle.culc_overlapped_area(fj.rectangle)
                    if overlapped is not None:
                        if overlapped == fi.rectangle:
                            remove_idx.append(i)
                        elif overlapped == fj.rectangle:
                            remove_idx.append(j)
        self.frames = [
            frame for i, frame in enumerate(self.frames) if i not in remove_idx
        ]

    def combine_nearby_frames(self, x_expansion, y_expansion):
        result = []
        expanded = [
            FrameBuffer(
                rectangle=frame.rectangle.expand(x_expansion, y_expansion),
                text=frame.text
            ) for frame in self.frames
        ]
        graph = OverlapGraph([frame.rectangle for frame in expanded])
        groups = graph.divide_groups()
        for group in groups:
            grouped_frames = [
                self.frames[i] for i in group
            ]
            grouped_rectangles = [
                gf.rectangle for gf in grouped_frames
            ]
            start_x = min([gr.start_x for gr in grouped_rectangles])
            start_y = min([gr.start_y for gr in grouped_rectangles])
            combined_rectangle = Rectangle(
                start_x=start_x,
                start_y=start_y,
                width=max(gr.start_x+gr.width for gr in grouped_rectangles)-start_x,
                height=max(gr.start_y+gr.height for gr in grouped_rectangles)-start_y
            )
            combined_text = ''
            for gf in sorted(grouped_frames, key=lambda gf: -gf.rectangle.start_x):
                combined_text += gf.text
            result.append(FrameBuffer(
                rectangle=combined_rectangle,
                text=combined_text
            ))
        self.frames = result

    def to_dict(self):
        return {
            PagesHeader.source.value: self.source,
            PagesHeader.page_id.value: self.page_id,
            PagesHeader.frames.value: len(self.frames)
        }

    def frames_to_dicts(self):
        return [
            frame.to_dict(self.source, self.page_id, frame_id) for frame_id, frame in enumerate(self.frames)
        ]


class FrameBuffer:
    def __init__(self, rectangle, text):
        self.rectangle = rectangle
        self.text = text

    def remove_charactors(self, charactors):
        for ch in charactors:
            self.text = self.text.replace(ch, '')

    def to_dict(self, source, page_id, frame_id):
        return {
            FramesHeader.source.value: source,
            FramesHeader.page_id.value: page_id,
            FramesHeader.frame_id.value: frame_id,
            FramesHeader.start_x.value: self.rectangle.start_x,
            FramesHeader.start_y.value: self.rectangle.start_y,
            FramesHeader.width.value: self.rectangle.width,
            FramesHeader.height.value: self.rectangle.height,
            FramesHeader.text.value: self.text
        }


class CSVProcessor:
    def __init__(self):
        self.pages = []

    def read(self, pages_path, frames_path):
        all_frames = {}
        with open(frames_path, mode='r', newline='') as frames_fp:
            frames_reader = csv.DictReader(frames_fp)
            for frame in frames_reader:
                key = (frame[FramesHeader.source.value], int(frame[FramesHeader.page_id.value]))
                if key not in all_frames:
                    all_frames[key] = []
                all_frames[key].append(FrameBuffer(
                    rectangle=Rectangle(
                        start_x=int(frame[FramesHeader.start_x.value]),
                        start_y=int(frame[FramesHeader.start_y.value]),
                        width=int(frame[FramesHeader.width.value]),
                        height=int(frame[FramesHeader.height.value])
                    ),
                    text=frame[FramesHeader.text.value]
                ))
        with open(pages_path, mode='r', newline='') as pages_fp:
            pages_reader = csv.DictReader(pages_fp)
            for page in pages_reader:
                key = (page[PagesHeader.source.value], int(page[PagesHeader.page_id.value]))
                frames = all_frames[key] if key in all_frames else []
                self.pages.append(PageBuffer(
                    source=key[0],
                    page_id=key[1],
                    frames=frames
                ))

    def add_page(self, page):
        self.pages.append(page)

    def remove_mini_frames(self, min_w=15, min_h=15):
        buffer = copy.deepcopy(self)
        for page in buffer.pages:
            page.remove_mini_frames(min_w, min_h)
        return buffer

    def remove_inclusion_frames(self):
        buffer = copy.deepcopy(self)
        for page in buffer.pages:
            page.remove_inclusion_frames()
        return buffer

    def combine_nearby_frames(self, x_expansion=3, y_expansion=0):
        buffer = copy.deepcopy(self)
        for page in buffer.pages:
            page.combine_nearby_frames(x_expansion, y_expansion)
        return buffer

    def remove_noise_charactors(self, charactors=list('、。])）」|\\/一')):
        buffer = copy.deepcopy(self)
        for page in buffer.pages:
            for frame in page.frames:
                frame.remove_charactors(charactors)
        return buffer

    def write(self, pages_path, frames_path):
        opfp = open(pages_path, 'w', newline='')
        offp = open(frames_path, 'w', newline='')
        opwriter = csv.DictWriter(opfp, fieldnames=[col.value for col in PagesHeader])
        opwriter.writeheader()
        ofwriter = csv.DictWriter(offp, fieldnames=[col.value for col in FramesHeader])
        ofwriter.writeheader()
        for page in self.pages:
            opwriter.writerow(page.to_dict())
            for row in page.frames_to_dicts():
                ofwriter.writerow(row)
        opfp.close()
        offp.close()

    def n_frames(self):
        return sum([len(page.frames) for page in self.pages])
