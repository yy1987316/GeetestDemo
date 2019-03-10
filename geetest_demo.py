import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from PIL import Image
from io import BytesIO

EMAIL = 'test@test.com'
PWD = '123456'
BORDER = 6
INIT_LEFT = 60

class CrackGeetest():
    def __init__(self):
        self.url = 'https://auth.geetest.com/login/'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.email = EMAIL
        self.pwd = PWD

    def __del__(self):
        self.browser.close()

    def get_geetest_button(self):
        """
        获取点击的验证码的按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_radar_tip')))
        return button

    def get_screenshot(self):
        """
        获取网页截图
        :return:
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_position(self):
        """
        获取验证码位置
        :return:
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_img')))
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return top, bottom, left, right

    def get_geetest_image(self, name='captcha.png', full=False):
        """
        获取验证码图片
        :param name:
        :return:
        """
        if full:
            self.browser.execute_script(
                'document.getElementsByClassName("geetest_canvas_fullbg")[0].setAttribute("style","")')
        else:
            self.browser.execute_script(
                'document.getElementsByClassName("geetest_canvas_fullbg")[0].setAttribute("style","display: none")')

        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha

    def get_slider(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        return slider

    def open(self):
        """
        打开页面，输入用户名密码
        :return:
        """
        self.browser.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.XPATH, '//form/div[1]//input')))
        pwd = self.wait.until(EC.presence_of_element_located((By.XPATH, '//form/div[2]//input')))
        email.send_keys(self.email)
        pwd.send_keys(self.pwd)

    def get_gap(self, image1, image2):
        """
        对比image1和image2，获取缺口偏移量
        :param image1:
        :param image2:
        :return:
        """
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断image1和image2中的(x, y)像素是否一样
        :param image1:
        :param image2:
        :param x:
        :param y:
        :return:
        """
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                        pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_track(self, distance):
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                a = 10
            else:
                a = -5

            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(move)
        return track

    def move_to_gap(self, slider, track):
        # 点住
        ActionChains(self.browser).click_and_hold(slider).perform()
        # 右滑
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def login(self):
        submit = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//form//button')))
        submit.click()
        time.sleep(10)
        print('登录完成')

    def crack(self):
        # 输入用户名密码
        self.open()
        # 1
        button = self.get_geetest_button()
        button.click()
        time.sleep(0.5)
        # 获取验证码图片
        image1 = self.get_geetest_image('captcha1.png', True)
        # 获取带缺口的验证码图片
        image2 = self.get_geetest_image('captcha2.png')
        # 获取缺口位置
        gap = self.get_gap(image1, image2)
        print('缺口位置', gap)
        # 减去缺口位移
        gap -= BORDER
        # 获取移动轨迹
        track = self.get_track(gap)
        print('滑动轨迹', track)
        # 拖动滑块
        slider = self.get_slider()
        self.move_to_gap(slider, track)

        success = self.wait.until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'geetest_success_radar_tip_content'), '验证成功'))
        print(success)

        if success:
            self.login()


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()