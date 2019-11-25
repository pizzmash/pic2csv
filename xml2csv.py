from xml.etree import ElementTree
import pathlib
import argparse
import sys
import csv
from pic2csv import pack_frame_info, pack_page_info


def search_xml_files(directories, regex):
    files = []
    for d in directories:
        p_temp = pathlib.Path(d)  # you die if d does'nt exist
        files += sorted([str(p) for p in p_temp.glob(regex)])
    return files


def convert_to_csv(files):
    page_fields = ['source', 'page_id', 'frames']
    frame_fields = ['source', 'page_id', 'frame_id', 'startX', 'startY', 'width', 'height', 'text']
    pages_fp = open('pages.csv', 'w', newline='')
    frames_fp = open('frames.csv', 'w', newline='')
    pages_csv = csv.DictWriter(pages_fp, fieldnames=page_fields)
    pages_csv.writeheader()
    frames_csv = csv.DictWriter(frames_fp, fieldnames=frame_fields)
    frames_csv.writeheader()

    for page_id, path in enumerate(files):
        tree = ElementTree.parse(path)
        root = tree.getroot()
        page = root.findall('PageData')[0]
        source = page.findall('FileName')[0].text
        size = page.findall('ImageSize')[0]
        page_width = int(size.findall('Width')[0].text)
        page_height = int(size.findall('Height')[0].text)

        dialogs = page.findall('DialogData')[0]
        page_info = pack_page_info(source, page_id, dialogs)
        pages_csv.writerow(page_info)
        for frame_id, dialog in enumerate(dialogs):
            vertices = []
            for point in dialog.findall('Coordinate')[0]:
                x = int(float(point.findall('X')[0].text) * page_width)
                y = int(float(point.findall('Y')[0].text) * page_height)
                vertices.append([x, y])
            start_x = min([v[0] for v in vertices])
            start_y = min([v[1] for v in vertices])
            width = max([v[0] for v in vertices]) - start_x
            height = max([v[1] for v in vertices]) - start_y
            text = dialog.findall('Text')[0].text
            frame = [[start_x, start_y, width, height], text]
            frame_info = pack_frame_info(source, page_id, frame_id, frame)
            frames_csv.writerow(frame_info)

    pages_fp.close()
    frames_fp.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--files',
        nargs='+',
        default=[],
        help='xml files'
    )
    parser.add_argument(
        '-d', '--directories',
        nargs='+',
        default=[],
        help='xml directories'
    )
    parser.add_argument(
        '-r', '--regex',
        default='*.xml',
        help='regular expression of the specified xml file'
    )
    args = parser.parse_args()

    files = args.files + search_xml_files(args.directories, args.regex)
    convert_to_csv(files)


if __name__ == "__main__":
    main()
