import sys
import time
import csv

import requests
import sendgrid

login_uni = "XXXXX"
password = "XXXXX#"
sendgrid_api_key = "XXXXX"
evaluation_list = [14631289, 14468405, 14662773, 14648182, 14468178, 14468284, 14631268, 14631162, 14468601, 14631417,
                   14631377]

email_from = "XXXXX"
email_reply_to = "XXXXX"
email_recipients = ["XXXXX", "XXXXX", "XXXXX", "XXXXX"]

######################################
# Code - Do not edit below this line #
######################################
# This should end with the current evaluation ID
cw_eval_uri = "https://courseworks.columbia.edu/direct/eval-reports/"

# The parameter here is the evaluation ID
cw_report_uri = "/report_view_report?mergeReports=true&evaluationId="
cw_report_uri2 = "&showSettingsDetail=false&canSelectGroups=false&returnTo=0&external=false&settingsByEvaluation=true" \
                 "&directView=false&viewmode=excluded&groupIds=" \
                 "&command+link+parameters%26Submitting%2520control%3DviewReportTop=Submit"

# No respondent URI, parameter here is evaluation ID.
cw_non_respondent = '/csvNonTakersReport?templateId=12314653&evaluateeId=excluded&filename=non_takers.csv&evalId='

web_worker = requests.session()
datetime = time.strftime('%x %H:%M:%S')


def login():
    # Generic Login Procedure
    payload = {
        '_username': login_uni,
        '_password': password
    }
    # Configure our session
    # Login to CourseWorks.
    web_worker.post('https://courseworks.columbia.edu/direct/session.json?', data=payload)
    # Get our SESSION info.
    response = web_worker.get('https://courseworks.columbia.edu/direct/session.json')
    if response.status_code != 200:
        print('Error: Received a non-200 response during login.')
        sys.exit(1)

    # Set reply to JSON and parse.
    reply_json = response.json()
    user_eid = reply_json['session_collection'][0]['userEid']
    if user_eid != login_uni:
        print('Error: Could not login as user ' + login_uni)
        sys.exit(1)

    print('Logged in as: ' + user_eid)


def get_reports():
    report = open('CourseWorks-NonTakers.csv', 'w')
    report.write("\"COURSE ID\",\"EMAIL\",\"NAME\"\n")
    for eval_id in evaluation_list:
        eval_id = str(eval_id)
        print("Getting report: " + eval_id)
        cw_preload_eval = ''.join([cw_eval_uri, eval_id, cw_report_uri, eval_id, cw_report_uri2])
        web_worker.get(cw_preload_eval)
        cw_fetch_csv = ''.join([cw_eval_uri, eval_id, cw_non_respondent, eval_id])
        csv = web_worker.get(cw_fetch_csv)
        report.write(csv.text)


def remove_exemptions():
    with open('Exemptions.csv', 'r') as exempt_csv:
        exempt = {row[0] for row in csv.reader(exempt_csv)}
    with open('CourseWorks-NonTakers.csv', 'r') as csv_in, \
            open('CourseWorks-NonTakersReport.csv', 'w', newline='') as report:
        writer = csv.writer(report)
        for row in csv.reader(csv_in):
            if row[0] not in exempt:
                writer.writerow(row)


def send_email():
    client = sendgrid.SendGridClient(sendgrid_api_key)
    message = sendgrid.Mail()
    for recipient in email_recipients:
        message.add_to(recipient)
    message.set_from(email_from)
    message.set_replyto(email_reply_to)
    message.set_subject("CourseWorks Evaluation Non-Takers Report as of " + datetime)
    message.set_html("This is an automated message. Attached is the evaluation non-takers report.<br>"
                     "Report time started: " + datetime + "<br>Report finished and sent: " +
                     time.strftime('%x %H:%M:%S') + "<br>Contact Ben if you have questions.")
    message.add_attachment('CourseWorks-NonTakersReport.csv', './CourseWorks-NonTakersReport.csv')
    client.send(message)


login()
get_reports()
remove_exemptions()
send_email()
