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


def read_source(source):
    # Check if the file on the web
    if len(parse.urlparse(source).scheme) > 0:
        try:
            res = requests.get(source)
        except requests.exceptions.RequestException as e:
            print('ERROR: {}'.format(e))
            return None
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(dir='./') as f:
            f.write(res.content)
            f.file.seek(0)
            image = cv2.imread(f.name, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(source, cv2.IMREAD_COLOR)
    if image is None:
        print('ERROR: Failed to read image')
        return None
    else:
        return image


def recognize_source(source):
    image = read_source(source)
    if image is None:
        return None
    else:
        r = recognize_captcha(settings.AP, [image])
        if r is None:
            return None
        else:
            response = json.loads(r)['responses'][0]
            frames = parse_response(response)
            return frames


def pack_page_info(source, page_id, frames):
    page_info = {}
    page_info['source'] = source
    page_info['page_id'] = page_id
    page_info['frames'] = len(frames) if frames is not None else None
    return page_info


def pack_frame_info(source, page_id, frame_id, frame):
    frame_info = {}
    frame_info['source'] = source
    frame_info['page_id'] = page_id
    frame_info['frame_id'] = frame_id
    frame_info['startX'] = frame[0][0]
    frame_info['startY'] = frame[0][1]
    frame_info['width'] = frame[0][2]
    frame_info['height'] = frame[0][3]
    frame_info['text'] = frame[1]
    return frame_info


def pack_error_info(source, page_id):
    return {'source': source, 'page_id':page_id}


def make_csv(sources):
    page_fields = ['source', 'page_id', 'frames']
    frame_fields = ['source', 'page_id', 'frame_id', 'startX', 'startY', 'width', 'height', 'text']
    error_fields = ['source', 'page_id']
    pages_fp = open('pages.csv', 'w', newline='')
    frames_fp = open('frames.csv', 'w', newline='')
    errors_fp = open('errors.csv', 'w', newline='')
    pages_csv = csv.DictWriter(pages_fp, fieldnames=page_fields)
    pages_csv.writeheader()
    frames_csv = csv.DictWriter(frames_fp, fieldnames=frame_fields)
    frames_csv.writeheader()
    errors_csv = csv.DictWriter(errors_fp, fieldnames=error_fields)
    errors_csv.writeheader()


    for i, source in enumerate(sources):
        print('({}/{}) FILE: {}'.format(i+1, len(sources), source))

        frames = recognize_source(source)

        page_info = pack_page_info(source, i, frames)
        pages_csv.writerow(page_info)

        if frames is not None:
            for j, frame in enumerate(frames):
                frame_info = pack_frame_info(source, i, j, frame)
                frames_csv.writerow(frame_info)
        else:
            error_info = pack_error_info(source, i)
            errors_csv.writerow(error_info)

        print()

    pages_fp.close()
    frames_fp.close()
    errors_fp.close()


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

    sources = args.images + search_images(args.directories)
    make_csv(sources)


if __name__ == "__main__":
    main()
