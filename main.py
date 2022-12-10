from cgitb import html
import re, json, datetime, time
from ssl import SSLSession
from threading import Thread
#from time import time
from traceback import print_tb
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests, bs4
from yattag import Doc

login_data = json.load(open('login.json'))
#driver = webdriver.Chrome('/Users/username/Downloads/chromedriver')
driver = webdriver.Chrome(login_data['working_path'] + '/chromedriver_win32/chromedriver')


login_url = 'https://t2schola.titech.ac.jp/'



##################################################################################################
# reset "categoryid" of login_url1 when each quarter ends. #######################################
##################################################################################################
login_url1 = 'https://t2schola.titech.ac.jp/course/index.php?categoryid=31'
##################################################################################################



login_url2 = 'https://portal.nap.gsic.titech.ac.jp/GetAccess/Login?Template=userpass_key&AUTHMETHOD=UserPassword'
login_url3 = 'https://portal.nap.gsic.titech.ac.jp/GetAccess/Login'
titech_url = 'https://portal.titech.ac.jp/'

user_name = login_data["account"]
user_password = login_data["password"]

login_submit = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[5]/td/input[1]'
user_name_xpath = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/input'
user_password_xpath = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[3]/td/div/div/input'

matrix_submit = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[8]/td/input[1]'
matrix1_xpath = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[4]/td/div/div/input'
matrix2_xpath = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[5]/td/div/div/input'
matrix3_xpath = '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[6]/td/div/div/input'
matrix_xpaths = [
    '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[4]/td/div/div/input',
    '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[5]/td/div/div/input',
    '/html/body/center[3]/form/table/tbody/tr/td/table/tbody/tr[6]/td/div/div/input'
]

driver.get('file:///C:' + login_data['working_path'] + '/index.html')
driver.switch_to.new_window('tab')
driver.get(login_url2)

driver.find_element_by_xpath(user_name_xpath).send_keys(user_name)
driver.find_element_by_xpath(user_password_xpath).send_keys(user_password)
driver.find_element_by_xpath(login_submit).click()

print(type(driver.page_source))

matrix_co_regex = re.compile(r'\[\w,\w\]')
matrix_coordinations = matrix_co_regex.findall(driver.page_source)

alp_matrix_ele_regex = re.compile(r'[A-Z]')
num_matrix_ele_regex = re.compile(r'[0-9]')
i = 0
while i < 3:
    matrix_chara_i = alp_matrix_ele_regex.findall(matrix_coordinations[i])
    matrix_num_i = num_matrix_ele_regex.findall(matrix_coordinations[i])
    driver.find_element(By.XPATH, value=matrix_xpaths[i]).send_keys(
        login_data['matrix'][int(matrix_num_i[0])][ord(matrix_chara_i[0]) - 65]
    )
    i += 1

driver.find_element_by_xpath(matrix_submit).click()

#chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
#driver = webdriver.Chrome(chrome_options=chrome_options)

# Move to T2SCHOLA page.
driver.find_element_by_xpath('/html/body/center/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]/a').click()
#
#print(driver.page_source)

s = requests.session()

for cookie in driver.get_cookies():
    s.cookies.set(cookie['name'], cookie['value'])

#res_t2schola = s.get('https://t2schola.titech.ac.jp/auth/eltitech/autologin.php')
res_t2schola = s.get(login_url1)
res_t2schola.raise_for_status()
#print(res_t2schola.text)
soup_t2 = bs4.BeautifulSoup(res_t2schola.text, 'html.parser')

course_ele_divs = soup_t2.find_all(class_="coursename")
#print('#################')
#print(course_ele_divs)
course_list = []
for coursename in course_ele_divs:
    for a in coursename.select("a"):
        course_link = a.get('href')
        #print(course_link)
        course_list.append({
            'course_name': a.get_text(),
            'course_link': course_link
        })

#print(course_list)

#################### fetching assignments from each page.
assignmentslist_in_courses = []
tmp_assignments_info_list = []
finished_assignments = []
unfinished_assignments = []
display_assignments = []

quizlist_in_courses = []
tmp_quiz_info_list = []
finished_quiz = []
unfinished_quiz = []
display_quiz = []

for a_course in course_list:
    res_a_course = s.get(a_course['course_link'])
    #print('res_a_course.text########')
    #print(res_a_course.text)
    soup_a_course = bs4.BeautifulSoup(res_a_course.text, 'html.parser')
    tmp_assignmentslist_ele_in_a_course = soup_a_course.select(".modtype_assign")

    tmp_quizlist_ele_in_a_course = soup_a_course.select(".modtype_quiz")
    
    if tmp_assignmentslist_ele_in_a_course + tmp_quizlist_ele_in_a_course == []:
        #print('\033[32m' + 'continue###############' + '\033[0m')
        continue
    #print('\033[32m' + 'tmp_assignmentslist_ele_in_a_course###########' + '\033[0m')
    #print(tmp_assignmentslist_ele_in_a_course)

    if tmp_quizlist_ele_in_a_course != []:
        for a_quiz in tmp_quizlist_ele_in_a_course:
            # quizの名前とリンク先
            a_quiz_name_and_link_ele = a_quiz.select('.aalink')
            if a_quiz_name_and_link_ele == []:
                continue
            quiz_name = a_quiz_name_and_link_ele[0].text
            quiz_link = a_quiz_name_and_link_ele[0].get('href')

            # quizのステータス
            a_quiz_status_ele = a_quiz.select('.btn-link img.icon')
            try:
                is_quiz_completed = a_quiz_status_ele[0].get('alt').startswith('完了: ')
            except:
                is_quiz_completed = False

            # 〆切をテキストから取得
            # response of a quiz link page.
            res_quiz_page = s.get(quiz_link)
            soup_of_quiz_page = bs4.BeautifulSoup(res_quiz_page.text, 'html.parser')
            deadline_ele_of_quiz_page = soup_of_quiz_page.select('.quizinfo')
            # example of deadline_ele_of_quiz_page :
            #
            # <div class="box py-3 quizinfo py-3"><p>受験可能回数: 1</p>
            # <p>この小テストは 2022年 12月 9日(金曜日) 15:25 から受験可能となりました。</p>
            # <p>この小テストの受験可能期間は 2022年 12月 13日(火曜日) 08:00 に終了します。</p>
            # </div>
            #print('\033[32m' + '##################' + '\033[0m')
            #print('\033[32m' + 'deadline ele of quiz page##################' + '\033[0m')
            #print(deadline_ele_of_quiz_page)
            #print('\033[32m' + '##################' + '\033[0m')

            mo2 = []
            deadline_regex = re.compile(r'(\d+)年 (\d+)月 (\d+)日.{5} (\d+):(\d+)')
            for an_ele in deadline_ele_of_quiz_page:
                #print("an_ele.text : " + an_ele.text)
                if "終了します。" in an_ele.text:
                    deadline_text = an_ele.text
                    mo2 = deadline_regex.findall(an_ele.text) # mo2 is a list
                    #print("mo2 : ")
                    #print(mo2)
                #print('\033[32m' + '##################' + '\033[0m')

            if mo2 == []:
                continue

            deadline_as_str = "" # deadline_as_str はソートに用いる
            for numstr in mo2[-1]:
                if len(numstr) == 1:
                    numstr = '0' + numstr # 12桁に揃える
                deadline_as_str = deadline_as_str + numstr

            a_quiz_info = {
                'course_name': a_course['course_name'],
                'course_link': a_course['course_link'],
                'assign_name': quiz_name,
                'assign_link': quiz_link,
                'deadline': deadline_text,
                'deadline_as_str': deadline_as_str,
                'status': is_quiz_completed
            }
            if is_quiz_completed:
                finished_quiz.append(a_quiz_info)
            else:
                unfinished_quiz.append(a_quiz_info)


    if tmp_assignmentslist_ele_in_a_course == []:
        continue # quizもassignmentもないとき

    # make assignments list including course, name, link, deadline and status. アサインメントのdictionaryを生成
    for a_assignment in tmp_assignmentslist_ele_in_a_course:
        #print('\033[32m' + 'a_assignment##################' + '\033[0m')
        #print(a_assignment)

        # get a assignment name and link
        a_assign_nameandlink_ele = a_assignment.select('.aalink')
        if a_assign_nameandlink_ele == []:
            #print('\033[32m' + 'continue###############' + '\033[0m')
            continue
        #print('\033[32m' + 'a_assign_nameandlink_ele##################' + '\033[0m')
        #print(a_assign_nameandlink_ele)

        #print('\033[32m' + '##################' + '\033[0m')
        #print('\033[32m' + 'a_assign_nameandlink_ele[0].text##################' + '\033[0m')
        #print(a_assign_nameandlink_ele[0].text)
        

        assign_name = a_assign_nameandlink_ele[0].text
        assign_link = a_assign_nameandlink_ele[0].get('href')

        a_assign_status_ele = a_assignment.select('.btn-link img.icon')

        try:
            is_assign_complted = a_assign_status_ele[0].get('alt').startswith('完了: ')
        except IndexError:
            is_assign_complted = False # まだチェックボックスが設定されていない課題などが該当

        # get the deadline. 〆切の取得
        res_assignpage = s.get(assign_link)
        soup_of_assignpage = bs4.BeautifulSoup(res_assignpage.text, 'html.parser')
        lastcol_ele_of_assignpage = soup_of_assignpage.select('tbody tr td.lastcol')
        #print('\033[32m' + 'lastcol##################' + '\033[0m')
        #print(lastcol_ele_of_assignpage)
        #dl_regex = re.compile(r'^(\d{4})年 (\d\d)月 (\d\d)日.{5} (\d\d):(\d\d)')
        #dl_year, dl_month, dl_day, dl_hour, dl_min = '0','0','0','0','0'
        #for column in lastcol_ele_of_assignpage:
        #    if column.text.startswith(r'\d{4}年'):
        #        dl_year, dl_month, dl_day, dl_hour, dl_min = dl_regex.search(column.text).groups()
        #        break
        #dl_year+'/'+dl_month+'/'+dl_day+' '+dl_hour+':'+dl_min
        deadline_text = lastcol_ele_of_assignpage[2].text
        
        # a 'deadline_as_list' exsample is :
        #   ['2022', '06', '16', '00', '10']
        #   ['2022', '06', '19', '00', '10']
        #   ['2022', '06', '23', '00', '00']
        #   ['2022', '06', '26', '00', '00']
        #   ['2022', '06', '30', '00', '00']
        #   ['2022', '06', '16', '12', '00']
        #   ['2022', '06', '20', '14', '20']
        #   ['2022', '06', '23', '14', '20']
        #   ['2022', '06', '27', '14', '20']
        #   ['2022', '06', '30', '12', '00']
        #   ['2022', '07', '4', '12', '00']
        #   ['2022', '07', '7', '12', '00']
        #

        deadline_as_list = re.compile(r'\d{1,4}').findall(deadline_text)
        if deadline_as_list == []:
            deadline_text = lastcol_ele_of_assignpage[3].text
            deadline_as_list = re.compile(r'\d{1,4}').findall(deadline_text)
            if deadline_as_list == []:
                print("ALERT: deadline is empty.")
                continue
        

        deadline_as_str = "" # deadline_as_str はソートに用いる
        for numstr in deadline_as_list:
            if len(numstr) == 1:
                numstr = '0' + numstr # 12桁に揃える
            deadline_as_str = deadline_as_str + numstr

        #print(deadline_as_list)
        
        #print(deadline_as_str)
        #deadline_as_datetime = datetime.datetime.strptime(deadline_as_str, '%Y%m%d%H%M')
        #print(deadline_as_datetime)
        #delta = datetime.datetime.now() - deadline_as_datetime
        #if delta.days > 30:
        #    continue

        a_assgin_info = {
            'course_name': a_course['course_name'],
            'course_link': a_course['course_link'],
            'assign_name': assign_name,
            'assign_link': assign_link,
            'deadline': deadline_text,
            'deadline_as_str': deadline_as_str,
            'status': is_assign_complted
        }

        #print(a_assgin_info)
        if is_assign_complted:
            finished_assignments.append(a_assgin_info)
            #print('finished')
        else:
            unfinished_assignments.append(a_assgin_info)
            #print('unfinished')
            #print(deadline_text)
            #print(deadline_as_str)
        
        #if -14 < delta.days and delta.days < 7:
        #    display_assignments.append(a_assgin_info)

#print('\033[32m')
#print(finished_assignments)
#print(unfinished_assignments)
#print('\033[0m')



display_assignments = unfinished_assignments + unfinished_quiz

# Sort assignment-list.
display_assignments.sort(key=lambda x: x['deadline_as_str'])#, reverse=True)

# generating HTML page of an assignment-list page.
doc, tag, text = Doc().tagtext()

with tag('head'):
    with tag('style'):
            doc.asis('.assignment {padding-top: 10px; border: solid 10px}')
with tag('html'):
    with tag('body'):
        with tag('div', klass='tile'):
            with tag('h1'):
                text('課題一覧@' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M'))
        with tag('div', klass='contents'):
            for assignment_obj in display_assignments:
                with tag('div', klass='assignments'):
                    with tag('div', klass='assignment'):
                        #with tag('div', klass='timer'):

                        with tag('a', klass='course_link', href=assignment_obj['course_link']):
                            with tag('div', klass='course_name'):
                                text(assignment_obj['course_name'])
                        with tag('a', klass='assign_link', href=assignment_obj['assign_link']):
                            with tag('div', klass='assign_name'):
                                text(assignment_obj['assign_name'])
                        with tag('div', klass='status'):
                            text(assignment_obj['status'])

                        with tag('div', klass='deadline'):
                            text(assignment_obj['deadline'])

assignments_index_page = open('./index.html', 'w')
assignments_index_page.write(doc.getvalue())
assignments_index_page.close()

handle_array = driver.window_handles
driver.switch_to.window(handle_array[0])
#driver.get('file:///C:' + login_data['working_path'] + '/index.html')
driver.refresh()


counter = 0
halt_time = 3
while True:
    try:
        _ = driver.window_handles
        #if counter > 300:
        #    driver.refresh()
        #    counter = 0
    except selenium.common.exceptions.InvalidSessionIdException as e:
        driver.quit()
    #driver.implicitly_wait(halt_time)
    time.sleep(halt_time)
    if counter > 1800:
        counter = 0
    #print('loop end')
    counter += halt_time
