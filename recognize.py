# coding: UTF-8
import base64
import json
import requests
import cv2
from processor import FrameBuffer, Rectangle


def recognize_captcha(api_key, images, logger):
    str_url = "https://vision.googleapis.com/v1/images:annotate"
    str_headers = {'Content-Type': 'application/json'}

    img_requests = []
    for img in images:
        _, dst_data = cv2.imencode('.jpg', img)
        str_encode_file = base64.b64encode(dst_data).decode('utf-8')
        img_requests.append({
            'image': {
                'content': str_encode_file
            },
            'features': [{
                    'type': 'DOCUMENT_TEXT_DETECTION',
            }]
        })

    obj_response = requests.post(
        str_url,
        data=json.dumps({"requests": img_requests}).encode(),
        params={'key': api_key},
        headers=str_headers
    )

    try:
        obj_response.raise_for_status()
    except Exception as e:
        logger.error('ERROR: {}'.format(e))
        return None
    return obj_response.text


def check_legality(vertices):
    for v in vertices:
        if "x" not in v or "y" not in v:
            return False
        elif v["x"] < 0 or v["y"] < 0:
            return False
    return True


def parse_response(response):
    frames = []
    if "fullTextAnnotation" in response:
        for page in response["fullTextAnnotation"]["pages"]:
            for block in page["blocks"]:
                vertices = block["boundingBox"]["vertices"]
                if not check_legality(vertices):
                    continue
                start_x = min([v["x"] for v in vertices])
                start_y = min([v["y"] for v in vertices])
                width = max([v["x"] for v in vertices]) - start_x
                height = max([v["y"] for v in vertices]) - start_y
                texts = ""
                for paragraph in block["paragraphs"]:
                    text = ""
                    for word in paragraph["words"]:
                        word_text = ''.join([
                            symbol["text"] for symbol in word["symbols"]
                        ])
                        text += word_text
                    texts += text
                frames.append(FrameBuffer(
                    rectangle=Rectangle(
                        start_x=start_x,
                        start_y=start_y,
                        width=width,
                        height=height
                    ),
                    text=texts
                ))
    return frames


if __name__ == '__main__':
    pass
