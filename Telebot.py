import calendar_details
import requests
from urllib.request import urlopen
import time


# main function
def internet_on():
    # Checks to see if you have an internet connection
    try:
        response = urlopen('https://www.google.com/')
        response.close()
        return True
    except Exception as e:
        print('No internet', e)


def check_internet():
    if internet_on() and calendar_details.run_check():
        print('You have internet and I am about to check assignments')
        telegramHandler()
    else:
        while True:
            print("Check internet connection or maybe it is not the as time yet, will check again in 100 seconds")
            time.sleep(300)  # sleep for 5 minutes
            check_internet()


def telegramHandler():
    data = calendar_details.getCalendarDetails()
    api_key_and_chatid = data[len(data) - 1]
    chatid = api_key_and_chatid[0]
    api_key = api_key_and_chatid[1]
    header = 'New assignment(s) are added for: %0A'
    body = ''
    if len(data) == 1 and calendar_details.readJsonFile()["updateOnNewAssignmentOnly"]:
        calendar_details.calcnextruntime()
        return
    if len(data) == 1:  # the list is never empty, so I set what zero is.
        answer = 'No new assignments added'
        # paste the link below to send the message using a telegram BOT
        requests.get('https://api.telegram.org/bot' + api_key + '/sendMessage?chat_id=' + chatid + '&text=' + answer)
        calendar_details.calcnextruntime()
        return
    end = len(data) - 1
    slicelist = data[0:end]
    for item in slicelist:
        # This was done repalce & because it would cut the string when sending message
        body += item.replace('&', 'and') + '%0A'
        answer = header + body
        requests.get('https://api.telegram.org/bot' + api_key + '/sendMessage?chat_id=' + chatid + '&text=' + answer)

    calendar_details.calcnextruntime()


check_internet()
