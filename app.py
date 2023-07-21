import json
from flask import Flask, request
import os
import ddddocr

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route("/code", methods=["POST"], endpoint="recognize")
def vcode():
    img = request.data
    ocr = ddddocr.DdddOcr()
    res = ocr.classification(img)
    return json.dumps({"code": 200, "msg": f"{res}"})


if __name__ == '__main__':
    app.config["LOG_FILE_PATH"] = os.path.join("./log/api_log.txt")
    print("*" * 1000)
    app.run(host="0.0.0.0", port=5000, debug=True)
