import json
import sys
import time
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


# replace transparent background
def replace_color(img, src_clr, dst_clr):
    img_arr = np.asarray(img, dtype=np.double)
    r_img = img_arr[:, :, 0].copy()
    g_img = img_arr[:, :, 1].copy()
    b_img = img_arr[:, :, 2].copy()

    img = r_img * 256 * 256 + g_img * 256 + b_img
    src_color = src_clr[0] * 256 * 256 + src_clr[1] * 256 + src_clr[2]

    r_img[img == src_color] = dst_clr[0]
    g_img[img == src_color] = dst_clr[1]
    b_img[img == src_color] = dst_clr[2]

    dst_img = np.array([r_img, g_img, b_img], dtype=np.uint8)
    dst_img = dst_img.transpose(1, 2, 0)

    return dst_img


# handle bg
def changeImg(imgpath: str, savepath: str):
    img = imgpath
    img = Image.open(img).convert('RGB')
    res_img = img.copy()
    count = 20
    for i in range(count):
        print(i)
        dst_img = replace_color(img, (255, 252, 248), (255, 255, 255))
        res_img = dst_img
    res_img = Image.fromarray(res_img)
    res_img.save(savepath)
    return savepath


def slice_image(image_path, save_path, min_with, min_height):
    path = 'img'
    if not os.path.exists(path):
        os.mkdir(path)
    with Image.open(image_path) as img:
        width, height = img.size
        slice_size = (min_with, min_height)
        slices = []
        for i in range(0, width + 1, slice_size[0]):
            for j in range(0, height + 1, slice_size[1]):
                box = (i, j, i + 120 - 1, j + 169 - 1,)
                slices.append(img.crop(box))
                img.crop(box).save(f'{save_path}/{i}px {j}px.png')
        return slices


def handle(coordinate_list: list, save_path: str):
    images = []
    x = 0
    y = 0
    for i in coordinate_list:
        x = i[0]
        y = i[1]
        x_x = x * 119
        x_y = y * 168
        img_name = './img/' + i[-1] + '.png'
        img = Image.open(img_name)
        images.append([x_x, x_y, img])

    large_image_width = 1190
    large_image_height = 1680

    large_image = Image.new('RGBA', (large_image_width, large_image_height), (255, 255, 255, 255))

    small_image_width = 119
    small_image_height = 168

    for coordinates in images:
        x1, y1 = coordinates[0], coordinates[1]
        img = coordinates[2]
        x2, y2 = x1 + small_image_width, y1 + small_image_height
        large_image.paste(img, (x1, y1, x2, y2))

    large_image.save(save_path)


def bg_download(bg_url, bg_f):
    bg_res = requests.get("http://c.gb688.cn/bzgk/gb/" + bg_url)
    headers = dict(bg_res.headers)
    filename = headers.get("Content-Disposition").split("filename=")[-1]
    with open(bg_f, 'wb') as f:
        f.write(bg_res.content)
        f.close()
    return bg_f


class Online(object):
    def __init__(self, driver):
        self.chrome_options = Options()
        self.driver = driver if driver else webdriver.Chrome(
            executable_path='chromedriver',
            options=self.chrome_options)

    def deal_with(self):
        try:
            time.sleep(2)
            pages = self.driver.find_element("xpath", "//*[@id='numPages']").text
            pages = int(pages.split("/")[-1])
            for page in range(0, pages):
                sp_list = self.driver.find_elements("xpath", f"//*[@id='{page}']//span")
                bg_url = self.driver.find_element("xpath", f"//*[@id='{page}']").get_attribute("bg")
                if not bg_url:
                    bg_url = sp_list[0].get_attribute("style").split(";")[1].split(": ")[-1].replace('url("',
                                                                                                     "").replace('")',
                                                                                                                 "")
                bg_f = bg_url.split("=")[-1] + ".png"
                bg_path = "./bg/"
                bg_f = bg_path + bg_f
                if not os.path.exists(bg_f):
                    bg_download(bg_url, bg_f)
                    changeImg(bg_f, bg_f)
                min_with = 120
                min_height = 169
                slice_save_path = "./img/"
                slice_image(bg_f, slice_save_path, min_with, min_height)
                page_coordinate = []
                for sp in sp_list:
                    cs = sp.get_attribute("class").split("-")
                    x, y = cs[-2], cs[-1]
                    st = sp.get_attribute("style").split(";")
                    px = st[0].split(": ")[-1]
                    page_coordinate.append([int(x), int(y), px.replace("-", "")])
                save_img_path = "./images/"
                save_img_single = save_img_path + f"{page}.png"
                handle(page_coordinate, save_img_single)
                self.driver.find_element("xpath", "//*[@id='next']").click()
        except Exception as e:
            print(e)
        finally:
            pass

    def verifyCode(self):
        time.sleep(3)
        byt = self.driver.find_element("xpath", "//*[@id='myModal']/div/div/div[2]/img").screenshot_as_png
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        #
        res = requests.post("http://app:port/code", data=byt, headers=headers, verify=False)
        print(res.text)
        res = json.loads(res.text)
        res = res.get("msg")
        try:
            self.driver.find_element("xpath", "//*[@id='verifyCode']").send_keys(res)
            time.sleep(0.5)
            self.driver.find_element("xpath", "//*[@id='myModal']/div/div/div[3]/button").click()
            try:
                # Capture popup
                dig_alert = self.driver.switch_to.alert
                if dig_alert:
                    self.driver.find_element("xpath", "//*[@id='myModal']/div/div/div[2]/span[1]").click()
                    byt = self.driver.find_element("xpath", "//*[@id='myModal']/div/div/div[2]/img").screenshot_as_png
                    headers = {
                        'Content-Type': 'application/octet-stream'
                    }
                    res = requests.post("http://host:port/code", data=byt, headers=headers, verify=False)
                    print(res.text)
                    res = json.loads(res.text)
                    res = res.get("msg")
                    self.driver.find_element("xpath", "//*[@id='verifyCode']").send_keys(res)
                    time.sleep(0.5)
                    self.driver.find_element("xpath", "//*[@id='myModal']/div/div/div[3]/button").click()
            except:
                pass
            return True
        except Exception as e:
            print(e)
            return False


def get_content(url: str):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        executable_path='./chromedriver',
        options=chrome_options)
    ol = Online(driver)
    ol.driver.maximize_window()
    ol.driver.get(url)
    is_ok = ol.verifyCode()
    content = None
    if is_ok:
        content = ol.deal_with()
    driver.close()
    return content


def convert_images_to_pdf(images_folder, pdf_file):
    images = []
    filelist = sorted(os.listdir(images_folder))
    for file in filelist:
        if file.endswith(".jpg") or file.endswith(".png"):
            image = Image.open(os.path.join(images_folder, file))
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            images.append(image)
            os.remove(os.path.join(images_folder, file))
    images[0].save(pdf_file, save_all=True, append_images=images[1:])
    return pdf_file


def main(hcno: str, bzh: str):
    url = f"http://c.gb688.cn/bzgk/gb/showGb?type=online&hcno={hcno}"
    get_content(url)
    attachment = convert_images_to_pdf('./images/', f"{bzh}.pdf")
    return attachment


if __name__ == '__main__':
    PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
    path = ['/GB/bg/', '/GB/img/', '/GB/images/']
    for ph in path:
        if not os.path.exists(PROJECT_DIR + ph):
            os.makedirs(PROJECT_DIR + ph)
    main("6E73010377EDEBC59C97507A41C15810", "BZH")
