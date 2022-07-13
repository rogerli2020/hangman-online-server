import base64
import requests
import json
import random
from PIL import Image
from io import BytesIO

NEW_IMAGE_HEIGHT = 100

class ImageFetcher:

    def __init__(self) -> None:
        pass

    def get_url_from_keyword(self, keyword, count=1):
        # TODO Always returns porno for some reason. Consider using another API.
        response = requests.get("http://api.flickr.com/services/feeds/photos_public.gne?jsoncallback=?",
            {
                "tags": keyword,
                "tagmode": "all",
                "format": "json",
            }
        )
        if response.status_code == 200:
            t = response.text[1:]
            t = t[:-1]
            t = json.loads(t)
            img_pool = []
            for i in t["items"]:
                m = i['media']['m'].replace("_m", "_b")
                img_pool.append(m)
            random.shuffle(img_pool)
            res = []
            for _ in range(0,count):
                if len(img_pool) == 0:
                    break
                f = open('img.jpg','wb')
                f.write(requests.get(img_pool.pop()).content)
                f.close()
                im = Image.open("./img.jpg")
                width, height = im.size
                new_size = (int(width * (NEW_IMAGE_HEIGHT/height)), NEW_IMAGE_HEIGHT)
                new_im = im.resize(new_size)
                # new_im.show()
                buffered = BytesIO()
                new_im.save(buffered, format="JPEG")
                res.append(base64.b64encode(buffered.getvalue()).decode('utf-8'))
            return res
        else:
            return ["ERROR"]