# coding: UTF-8
import cv2
from recognize import recognize_captcha, parse_response
import json
import csv
import argparse
from urllib import parse
import tempfile
import requests
import pathlib
import imghdr
import settings


def search_images(directories):
    images = []
    for d in directories:
        p_temp = pathlib.Path(d)  # you die if d does'nt exist
        imgs = [str(p) for p in p_temp.iterdir() if p.is_file() and imghdr.what(str(p)) is not None]
        images += sorted(imgs)
    return images


def write_csv(sources):
    page_fields = ['source', 'page_id', 'frames']
    frame_fields = ['source', 'page_id', 'frame_id', 'startX', 'startY', 'width', 'height', 'text']
    pages_fp = open('pages.csv', 'w', newline='')
    frames_fp = open('frames.csv', 'w', newline='')
    pages_csv = csv.DictWriter(pages_fp, fieldnames=page_fields)
    pages_csv.writeheader()
    frames_csv = csv.DictWriter(frames_fp, fieldnames=frame_fields)
    frames_csv.writeheader()

    for i, source in enumerate(sources):
        print('({}/{}) file: {}'.format(i+1, len(sources), source))
        is_error = False
        image = None
        # check if the file on the web
        if len(parse.urlparse(source).scheme) > 0:
            res = None
            try:
                res = requests.get(source)
            except requests.exceptions.RequestException as e:
                print('error: {}'.format(e))
            if res is not None:
                with tempfile.NamedTemporaryFile(dir='./') as f:
                    f.write(res.content)
                    f.file.seek(0)
                    image = cv2.imread(f.name, cv2.IMREAD_COLOR)
        else:
            image = cv2.imread(source, cv2.IMREAD_COLOR)

        if image is None:
            print('error: failed to read image')
            is_error = True
        else:
            r = recognize_captcha(settings.AP, [image])
            if r is None:
                is_error = True
            else:
                response = json.loads(r)['responses'][0]
                frames = parse_response(response)

        page_info = {}
        page_info['page_id'] = i
        page_info['source'] = source
        page_info['frames'] = len(frames) if not is_error else None
        pages_csv.writerow(page_info)

        if not is_error:
            for j, frame in enumerate(frames):
                # startX, startY, width, height
                frame_info = {
                    frame_fields[frame_fields.index('startX')+k]: val for k, val in enumerate(frame[0])
                }
                frame_info['source'] = source
                frame_info['page_id'] = i
                frame_info['frame_id'] = j
                frame_info['text'] = frame[1]
                frames_csv.writerow(frame_info)
        print()

    pages_fp.close()
    frames_fp.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--images',
        nargs='+',
        default=[],
        help='image files'
    )
    parser.add_argument(
        '-d', '--directories',
        nargs='+',
        default=[],
        help='image directories'
    )
    args = parser.parse_args()

    images = args.images + search_images(args.directories)

    write_csv(images)


if __name__ == "__main__":
    main()
