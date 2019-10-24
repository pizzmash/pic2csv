# coding: UTF-8
import base64
import json
import requests
import cv2


def recognize_captcha(api_key, images):
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
        print('error: {}'.format(e))
        return None
    return obj_response.text


def parse_response(response):
    frames = []
    for page in response["fullTextAnnotation"]["pages"]:
        for block in page["blocks"]:
            vertices = block["boundingBox"]["vertices"]
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
            frames.append(([start_x, start_y, width, height], texts))
    return frames


if __name__ == '__main__':
    pass
