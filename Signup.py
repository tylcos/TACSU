import random

import requests
import time

import PayloadGenerator


settings = {
    # CRNs to sign up for seperated by comma.
    'REQUESTED_CRNs': '',

    # SESSID Cookie. After copying the SESSID, close the browser tab where you copied it to
    # prevent the browser from using an old SESSID and signing you out.
    'SESSID': '',

    # Semester code.
    'SEMESTER': '202108',


    # Wait for time ticket to start before sending requests.
    'WAIT_FOR_TICKET': True,

    # Time that the time ticket starts.
    'TICKET_START_TIME': '8/18/2021 10:30',

    # Number of seconds before the time ticket starts to check for a valid time ticket.
    # Used in case the ticket starts early or your time is off from the server.
    'TICKET_CHECK_HEADSTART': 60,

    # Interval to check for time ticket start in seconds.
    # Begins checking TICKET_CHECK_HEADSTART seconds before TICKET_START_TIME.
    'TICKET_CHECK_INTERVAL': 5
}


def main():
    # Setup session object to imitate browser
    s = requests.Session()
    s.cookies['SESSID'] = settings['SESSID']
    s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    s.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    s.headers['Accept-Language'] = 'en-US,en;q=0.5'
    s.headers['Accept-Encoding'] = 'gzip, deflate, br8'
    s.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    s.headers['Origin'] = 'https://oscar.gatech.edu'
    s.headers['Referer'] = 'https://oscar.gatech.edu/'
    s.headers['Upgrade-Insecure-Requests'] = '1'
    s.headers['Connection'] = 'keep-alive'
    s.headers['Sec-Fetch-Dest'] = 'document'
    s.headers['Sec-Fetch-Mode'] = 'navigate'
    s.headers['Sec-Fetch-Site'] = 'same-origin'
    s.headers['Sec-Fetch-User'] = '?1'


    # Request current classes
    response = s.post('https://oscar.gatech.edu/pls/bprod/bwskfreg.P_AltPin', data={'term_in': settings['SEMESTER']})
    responseStr = str(response.content)

    # Check if login succesfull
    if '<h2>Add/Drop Classes: </h2>' not in responseStr:
        raise Exception('Error logging in')

    # Check if user has time ticket
    validTicket = '<h3>Current Schedule</h3>' in responseStr
    if not validTicket:
        if not settings['WAIT_FOR_TICKET']:
            raise Exception('Time ticket hasn\'t started yet. Enable WAIT_FOR_TICKET to wait until the ticket starts.')


        startTime = time.mktime(time.strptime(settings['TICKET_START_TIME'], "%m/%d/%Y %H:%M"))
        checkTime = startTime - settings['TICKET_CHECK_HEADSTART']
        sleepTime = checkTime - time.time()

        # Sleep until check for valid time ticket
        if sleepTime > 0:
            print(f'{round(sleepTime, 1)} seconds until check for valid time ticket.')
            time.sleep(sleepTime)

        # Start checking for valid time ticket
        response = s.post('https://oscar.gatech.edu/pls/bprod/bwskfreg.P_AltPin', data={'term_in': settings['SEMESTER']})
        responseStr = str(response.content)
        validTicket = '<h3>Current Schedule</h3>' in responseStr

        while not validTicket:
            time.sleep(settings['TICKET_CHECK_INTERVAL'] + random.uniform(-1, 1))

            timeUntilStart = startTime - time.time()
            if timeUntilStart > 0:
                print(f'Verified that the ticket hasn\'t started yet. {round(timeUntilStart, 1)} seconds until offical ticket start time.')
            else:
                print(f'Ticket should have started {round(-timeUntilStart, 1)} seconds ago, checking again.')

            response = s.post('https://oscar.gatech.edu/pls/bprod/bwskfreg.P_AltPin', data={'term_in': settings['SEMESTER']})
            responseStr = str(response.content)
            validTicket = '<h3>Current Schedule</h3>' in responseStr

        print('Verified ticket has started.')


    # Send payload to sign up for classes
    classPayload = PayloadGenerator.GenerateSignupPayload(responseStr)

    print(f'Sending request to sign up for {settings["REQUESTED_CRNs"]}')
    s.headers['Referer'] = 'https://oscar.gatech.edu/bprod/bwckcoms.P_Regs'
    response = s.post('https://oscar.gatech.edu/bprod/bwckcoms.P_Regs', data=classPayload)


    # Print final messages. Could easily parse the response to see if the classes were added succesfully.
    print('Request sent and received response code: ' + str(response.status_code))
    print('Exiting')


if __name__ == "__main__":
    main()
