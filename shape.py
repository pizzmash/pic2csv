import argparse
import csv
from logging import getLogger, StreamHandler, INFO

from processer import CSVProcesser
import settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_pages_csv',
        type=str,
        help='input pages CSV file'
    )
    parser.add_argument(
        'input_frames_csv',
        type=str,
        help='input frames CSV file'
    )
    parser.add_argument(
        'output_pages_csv',
        type=str,
        help='output pages CSV file'
    )
    parser.add_argument(
        'output_frames_csv',
        type=str,
        help='output frames CSV file'
    )
    args = parser.parse_args()

    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(INFO)
    logger.setLevel(INFO)
    logger.addHandler(handler)
    logger.propagate = False

    prcs = CSVProcesser()
    prcs.read(args.input_pages_csv, args.input_frames_csv)
    logger.info('count of frames: %d' % prcs.n_frames())
    logger.info('removing mini frames...')
    prcs = prcs.remove_mini_frames(settings.MIN_W, settings.MIN_H)
    logger.info('done!')
    logger.info('count of frames: %d' % prcs.n_frames())
    logger.info('removing inclusion frames...')
    prcs = prcs.remove_inclusion_frames()
    logger.info('done!')
    logger.info('count of frames: %d' % prcs.n_frames())
    logger.info('combining nearby frames...')
    prcs = prcs.combine_nearby_frames(settings.EXP_X, settings.EXP_Y)
    logger.info('done!')
    logger.info('count of frames: %d' % prcs.n_frames())
    logger.info('removing noise charactors')
    prcs = prcs.remove_noise_charactors(list(settings.NOISE_CHARS))
    logger.info('done!')
    prcs.write(args.output_pages_csv, args.output_frames_csv)


if __name__ == '__main__':
    main()
