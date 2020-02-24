# coding: UTF-8
import cv2
from recognize import recognize_captcha, parse_response
from processer import PageBuffer, CSVProcesser
import json
import argparse
from urllib import parse
import tempfile
import requests
import pathlib
import imghdr
import settings
import os
from logging import getLogger, FileHandler, StreamHandler, INFO


def search_images(directories):
    images = []
    for d in directories:
        p_temp = pathlib.Path(d)  # you die if d does'nt exist
        imgs = [str(p) for p in p_temp.iterdir() if p.is_file() and imghdr.what(str(p)) is not None]
        images += sorted(imgs)
    return images


def read_source(source, logger):
    # Check if the file on the web
    if len(parse.urlparse(source).scheme) > 0:
        try:
            res = requests.get(source)
        except requests.exceptions.RequestException as e:
            logger.error('ERROR: {}'.format(e))
            return None
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(dir='./') as f:
            f.write(res.content)
            f.file.seek(0)
            image = cv2.imread(f.name, cv2.IMREAD_COLOR)
    else:
        if not os.path.exists(source):
            logger.error('ERROR: file does not exist')
            return None
        else:
            image = cv2.imread(source, cv2.IMREAD_COLOR)
    if image is None:
        logger.error('ERROR: failed to read image')
        return None
    else:
        return image


def recognize_source(source, logger):
    image = read_source(source, logger)
    if image is None:
        return None
    else:
        r = recognize_captcha(settings.AP, [image], logger)
        if r is None:
            return None
        else:
            response = json.loads(r)['responses'][0]
            frames = parse_response(response)
            return frames


def make_csv(sources, output_pages_csv, output_frames_csv, logger):
    prcs = CSVProcesser()
    for i, source in enumerate(sources):
        logger.info('\n({}/{}) FILE: {}'.format(i+1, len(sources), source))
        frames = recognize_source(source, logger)
        if frames is None:
            frames = []
        prcs.add_page(PageBuffer(
            source=source,
            page_id=i,
            frames=frames
        ))
    prcs.write(output_pages_csv, output_frames_csv)


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
    parser.add_argument(
        '-p', '--pages',
        default='pages.csv',
        help='output pages CSV file'
    )
    parser.add_argument(
        '-f', '--frames',
        default='frames.csv',
        help='output frames CSV file'
    )
    args = parser.parse_args()

    logger = getLogger(__name__)
    sh = StreamHandler()
    sh.setLevel(INFO)
    fh = FileHandler('result.log')
    fh.setLevel(INFO)
    logger.setLevel(INFO)
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.propagate = False

    sources = args.images + search_images(args.directories)
    make_csv(sources, args.pages, args.frames, logger)


if __name__ == "__main__":
    main()
