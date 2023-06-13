from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from undetected_chromedriver import Chrome
from selenium.common.exceptions import *
import markdownify
import datetime
import time
import os

# 从env中读取账号密码
OPENAI_ACCOUNT = os.getenv("OPENAI_ACCOUNT")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")

class LoginPage:
    def __init__(self,driver:webdriver.Chrome):
        self.driver =  driver

    def pass_cloud_fire(self):
        '''某些梯子会触发cloud_fire,需要进行验证'''
        try:
            print("判断是否已经进入主页面")
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#prompt-textarea')))
            print("已经进入")
            return
        except:
            print("未进入")            

        
        try:
            print("等待cloudfire验证")
            time.sleep(10)
            iframe_element = self.driver.find_element(By.XPATH, '//iframe')
            self.driver.switch_to.frame(iframe_element)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'cf-stage'))).click()
            self.driver.switch_to.default_content()

            print("已经通过cloudfire的验证")
        except:
            print("没有cloudfire的验证")
            self.driver.switch_to.default_content()



    def login(self):
        '''登录到chatgpt网站'''
        self.driver.get("https://chat.openai.com/chat")
        self.driver.set_window_position(0,0)
        self.driver.set_window_size(600,800)
        # self.pass_cloud_fire()

        # time.sleep(5)
        # try: #防止有cookies,直接跳过
        #     if EC.presence_of_element_located((By.XPATH, '//div[text()="Log in"]')):
        #         # 登录
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[text()="Log in"]'))).click()
        #         time.sleep(3)
        #         # 输入账号
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input#username'))).send_keys(OPENAI_ACCOUNT)
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button._button-login-id'))).click()
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input#password'))).send_keys(OPENAI_PASSWORD)
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"]'))).click()

        #         # 进入界面
        #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn-neutral'))).click()
                
        #         while True:
        #             try:
        #                 WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.ml-auto'))).click()
        #                 break
        #             except:
        #                 print("next点击完成")
        #                 break

        #         while True:
        #             try:
        #                 WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.ml-auto'))).click()
        #                 break
        #             except:
        #                 print("done点击完成")
        #                 break


            
        # except NoSuchElementException:
        #     print("已经有cookie了,不做登录")



class HomePage:
    def __init__(self, driver:webdriver.Chrome):
        self.driver = driver
        self.answer_i = 0 #对gpt回答进行提取
        
        self.volite_button_locator = (By.XPATH,"//div[contains(text(),'Acknowledge')]")

    def _clean_prompt(self, prompt):
        import re
        '''清洗prompt为BMP'''
        
        # BMP字符范围为U+0000 - U+FFFF
        # 所以这个正则表达式可以匹配所有非BMP字符
        non_bmp_map = re.compile(u'[^\U00000000-\U0000FFFF]', re.UNICODE)

        # 使用空字符替换所有非BMP字符
        cleaned_prompt = non_bmp_map.sub('', prompt)

        return cleaned_prompt


    def get(self,prompt,mode=3.5):
        '''发送消息,并且获取为markdown格式'''

        # 清洗prompt为BMP
        prompt = self._clean_prompt(prompt)

        # 发送消息,并且处理1小时超时的情况
        self.send(prompt,mode)
                            
        # 提取消息
        answer = self._extra_html_answer(prompt,mode)
        answer = self._build_json(answer)

        print(answer)
        return answer         

    def send(self,prompt,mode=3.5):
    
            # 判断能否切换模式        
            self.check_and_swtich_mode(mode)

            # 刷新
            # self._open_new_conversation()

            # 发送消息
            self._send_pmt(prompt,mode)

            # 查看消息发送情况,等待消息显示
            start_time = datetime.datetime.now()
            while True:
                try:
                    # 成功发送            
                    if self.driver.find_element(By.CSS_SELECTOR,"span svg path[fill='currentColor']"):
                        print("完成发送prompt")
                        return 
                        
                except Exception:
                    # 重新发送
                    time.sleep(5)
                    print("等待回复,最多等待300s........")
                   
                    


                    if (datetime.datetime.now() - start_time).seconds > 300:  
                        print("chatgpt回复本次超时")

                        # 检查是否出现1小时请求过多的限制
                        if self._check_one_hour_limit():
                            print("等待10分钟")

                            i = 0
                            while i < 10 * 60:
                                time.sleep(1)
                                i += 1

                        self.answer_i = 0  
                        self._open_new_conversation()
                        self.send(prompt,mode)
                        return 


    def _send_pmt(self,prompt,mode):
        '''发送的点击动作,保证发送成功'''

        while True:
            try:
                print("开始发送prompt")
                text_box = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"textarea")))
                text_box.send_keys(prompt)
                time.sleep(1)
                WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"button.absolute.transition-colors"))).click()
                print("prompt发送完成")
                break
            
            except Exception as e:
                print("发送被打断,重试",e)
                self._open_new_conversation()
                self.check_and_swtich_mode(mode)
                


    def check_and_swtich_mode(self,mode):
        # 判断能否切换模式 
        if mode == 3.5:
            self._switch_gpt3()
        if mode == 4:
            self._switch_gpt4()

    def _switch_gpt3(self):
        try:
            if "gpt-4" not in self.driver.current_url:
                print("当前已经是gpt3.5模式")
                return
            print("尝试切换gpt-3.5")
            self._open_new_conversation()
            time.sleep(1)
            print("切换完成")
        except Exception as e:
            print("未切换模式",e)


    def _switch_gpt4(self):
        try:
            if "gpt-4-mobile" in self.driver.current_url:
                print("当前已经是gpt-4-mobile模式")
                return
            print("尝试切换gpt-4")
            self._open_new_conversation()
            print("切换完成")
        except Exception as e:
            print("未切换模式",e)


   
    def _check_one_hour_limit(self):
        '''检查too many request的情况'''
        print("判断是否请求过多")
        try:
            self.driver.find_element(By.XPATH,"//div[contains(text(),'hour')]")
            print("1小时,24小时内请求过多")
            return True
        except NoSuchElementException:
            print("未出现请求过多")
            return False


    def _open_new_conversation(self):
        # 重新点回到tab
        self.answer_i = 0

        while True:
            try:
                # print("刷新,开始打开新对话,等待5s,防止被ban")
                # self.driver.refresh()
                # time.sleep(5)

                # lp = LoginPage(self.driver)
                # lp.pass_cloud_fire()

                self.driver.get("https://chat.openai.com/?model=gpt-4-mobile")

                print("新对话创建完成")
                break
            except Exception as e:
                print("新对话没有寻找到元素,重试",e)




    def _extra_html_answer(self,prompt,mode):
        '''根据回答索引,提取网页的信息'''
        while True:
            try:
                print("开始提取网页消息")
                answer = self.driver.find_elements(By.CSS_SELECTOR,"div.light")[self.answer_i].text
                self.answer_i += 1 #提取到消息再变化
                print("提取网页消息成功")
                break
            except IndexError as e:
                print("提取网页消息的索引错误",e)
                self._open_new_conversation()
                self.send(prompt,mode)
            except Exception as e:
                print("提取消息未知错误",e)


        return answer

    def _build_json(self, answer):
        answer = answer.replace("\\n","").replace("\n","").replace("'","").replace("'''","")

        parts = answer.split("[{")
        if len(parts) > 1:
            answer = "{" +  "".join(parts[1:])
            answer = answer[:-1]

        parts = answer.split("{")
        if len(parts) > 1:
            answer =  "{" + "{".join(parts[1:])

        return answer

def lunch_driver():
    # 关闭chrome浏览器
    os.system("taskkill /f /im chrome.exe")
    
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=C:/Users/xiahan/Documents/BaiduSyncdisk/code/2_爬虫/chrome")
    driver = Chrome(options=options)

    

    return driver


def gpt_web_api():
    driver = lunch_driver()
    LoginPage(driver).login()
    return HomePage(driver)