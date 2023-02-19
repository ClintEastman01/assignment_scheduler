from datetime import datetime, timedelta
import json
import time
import calenderFunc
from playwright.sync_api import sync_playwright
from os.path import exists

upcoming = 'https://lms.manhattan.edu/calendar/view.php?view=upcoming'  # School's event page


def timefile(lastrun, nextrun):  # creates a new timefile that holds the last and next successful run of the script
    f = open("time.txt", "w")
    f.write(lastrun + '\n')
    f.write(nextrun + '\n')


def calcnextruntime():  # calculates the next time the program will be executed
    lasttime_ran = datetime.now()
    lasttime_ran_hour = int(datetime.strftime(lasttime_ran, '%H'))
    x = 24 - lasttime_ran_hour
    nextrun = lasttime_ran + timedelta(hours=x)
    nextrun = datetime.strftime(nextrun, '%m/%d/%y %H:%M:%S')
    lasttime_ran = datetime.strftime(lasttime_ran, '%m/%d/%y %H:%M:%S')
    timefile(lasttime_ran, nextrun)


def run_check():  # checks to see if the next run time in the given file has past if the file exist
    if not filexist("time.txt"):
        return True
    f = open("time.txt", "r")
    data = f.readlines()
    nextrun = data[1].replace('\n', '')
    nextrun = datetime.strptime(nextrun, '%m/%d/%y %H:%M:%S')
    if datetime.now() > nextrun:
        return True


def readJsonFile():  # reads data from editme.json and returns that a dict
    f = open('editme.json')
    data = json.load(f)
    f.close()
    return data


def utc_offset():
    # checkings to see if is currently daylight saying or not and returns the appropriate timezone for New_York
    UTC_offset = ""
    if time.daylight == 1:
        UTC_offset = "-05:00"
    else:
        UTC_offset = "-04:00"
    return UTC_offset


def convertUnixTime(link):
    # This takes the entire hmtl link for the date and time due of assignment and converts the unixc
    # time into readabale time
    start = link.find('time=')  # this searches the link for time=
    # this takes off the previsouly found string and only return the next 10 characters
    # which is the unixtime found in the link
    unixtime = int(link[start + 5: start + 15])
    dt_object = datetime.fromtimestamp(unixtime)  # converting unix time to readable time

    return dt_object


def detectClassNames(link):  # This takes hmtl output and searches the output  for id= in all the divs
    x = link.find('id=')
    if x == -1:
        return False
    else:
        return True


def filexist(path):  # check to see if a file exists
    if exists(path):
        return True


# Srapes the Moodle upcoming events page to find all upcoming assignments then passes the data to google calendar
def getCalendarDetails():
    fileinfo = readJsonFile()
    homeWorkDetails = []
    botinfo = []
    user = fileinfo['username']
    pwd = fileinfo['password']
    # calculates the number of days given into minutes so it can be passed to google calendar
    days_before_assignment_due_1 = fileinfo['days_before_assignment_due_1'] * 24 * 60
    days_before_assignment_due_2 = fileinfo['days_before_assignment_due_2'] * 24 * 60
    twofactcode = fileinfo['twofactcode']
    chatId = fileinfo['chatId']
    token = fileinfo['token']

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        if filexist('savedata'):
            context = browser.new_context(storage_state="savedata")
        else:
            context = browser.new_context()
        page = context.new_page()
        page.goto(upcoming)

        # skips normal login if there are cookies
        try:
            if page.wait_for_selector('#username', timeout=2000):
                page.fill('#username', user)
                page.fill('#password', pwd)
                page.click('[type=submit]')
                page.wait_for_selector(
                    '[type="submit"]')  # makes sure the authentication page loads before entering data
                page.click('[type="checkbox"]')  # selects the option to reminder the browser for 30 days
                page.click('#passcode')
                page.wait_for_selector('[class ="passcode-input"]')
                page.fill('[class ="passcode-input"]', twofactcode)
                page.click('#passcode')
        except Exception:
            print('Login skipped')

        page.wait_for_selector('[class ="current text-center"]')
        context.storage_state(path="savedata")  # stores the cookies in order to skill authentication everyting scrape
        page.wait_for_selector('[class="event mt-3"]')  # waiting for page to load
        all_upcoming_events = page.query_selector_all('[class="event mt-3"]')  # selecting the entire page
        events = '[class="name d-inline-block"]'  # selecting all events on page
        for item in all_upcoming_events:
            taskDetails = []
            task_name = item.query_selector(events).inner_text()
            task_type = item.get_attribute('data-event-component')  # all the information for all available assignments
            if task_type == 'mod_quiz':
                task_type = 'Quiz'
            if task_type == 'mod_assign':
                task_type = 'Assignment'
            if task_type == 'mod_turnitintooltwo':
                task_type = 'Turn in paper'
            unixdue_dates = item.query_selector(
                '[class="col-11"]').inner_html()  # passed the found like to convert time
            start_time = convertUnixTime(unixdue_dates)
            class_names = item.query_selector_all('[class="col-11"]')

            for i in class_names:
                if detectClassNames(i.inner_html()):
                    class_name = i.inner_text()

            end_time = start_time + timedelta(hours=1)
            taskDetails.append(task_name)
            taskDetails.append(task_type)
            taskDetails.append(class_name)
            taskDetails.append(start_time.strftime("%Y-%m-%dT%H:%M:%S" + utc_offset()))
            taskDetails.append(end_time.strftime("%Y-%m-%dT%H:%M:%S" + utc_offset()))
            taskDetails.append(days_before_assignment_due_1)
            taskDetails.append(days_before_assignment_due_2)
            homeWorkDetails.append(taskDetails)
        botinfo.append(chatId)
        botinfo.append(token)
        homeWorkDetails.append(botinfo)
        return calenderFunc.create_events(homeWorkDetails)


if __name__ == "__main__":
    pass
