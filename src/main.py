import getpass
import argparse
import os
import socket
from flask import Flask, make_response, send_file
from collections import defaultdict
from datetime import datetime, timedelta
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter, inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table
from reportlab.lib.styles import getSampleStyleSheet
from jira import JIRA

if 'JIRA_SERVER' in os.environ:
    server = os.environ['JIRA_SERVER']
else:
    server = input("Enter server (e.g. jira.example.com): ")

if 'JIRA_USER' in os.environ:
    username = os.environ['JIRA_USER']
else:
    username = input("Username (e.g. joe.doe): ")

if 'JIRA_USERPASSWORD' in os.environ:
    password = os.environ['JIRA_USERPASSWORD']
else:
    password = getpass.getpass("Password: ")


if 'JIRA_WORKLOG_FROM_DATE' in os.environ:
    from_date = datetime.strptime(os.environ['JIRA_WORKLOG_FROM_DATE'], '%Y-%m-%d').date()
else:
    from_date = datetime.strptime(input("From date (e.g. 2016-12-01): "), '%Y-%m-%d').date()

if 'JIRA_WORKLOG_TO_DATE' in os.environ:
    to_date = datetime.strptime(os.environ['JIRA_WORKLOG_TO_DATE'], '%Y-%m-%d').date()
else:
    to_date = datetime.strptime(input("To date (e.g. 2016-12-31): "),'%Y-%m-%d').date()


if 'JIRA_PROJECTID' in os.environ:
    project = os.environ['JIRA_PROJECTID']
else:
    project = input("JIRA Project ID: ")

parser = argparse.ArgumentParser()
parser.add_argument('--log', nargs='?', help='log')
args = parser.parse_args()


DATE_FORMAT = "%d/%m/%y"

app = Flask(__name__)

def get_worklog(assignee):

    jira = JIRA('https://{0}'.format(server),
                basic_auth=(username, password))
    jql = 'timespent > 0 AND project = %s ORDER BY updated DESC' % project 
    issues = jira.search_issues(jql)
        
    worklogs = []
    date_worklogs = defaultdict(list)
    issue_worklogs = defaultdict(list)
    issues_data = {}
    for issue in issues:
        issues_data[issue.key] = issue
        for w in jira.worklogs(issue.key):
            started = datetime.strptime(w.started[:-5],
                                        '%Y-%m-%dT%H:%M:%S.%f')
            author = w.author
            if author.name != assignee:
                continue

            if not (from_date <= started.date() <= to_date):
                continue

            spent = w.timeSpentSeconds / 3600

            worklog = {
                "started": started, "spent": spent, "author": author,
                "issue": issue,
            }
            worklogs.append(worklog)
            date_worklogs[started.date()].append(worklog)
            issue_worklogs[issue.key].append(worklog)

    ts = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, -1), 'DejaVuSans', 8, 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONT', (0, 0), (0, -1), 'DejaVuSans-Bold', 8, 8),
        ('FONT', (0, 0), (-1, 0), 'DejaVuSans-Bold', 8, 8),
    ]

    total_spent = 0.0

    def cell_value(col, row, date, issue):
        nonlocal total_spent

        is_weekend = date.weekday() >= 5 if date else None
        if is_weekend:
            ts.append(('BACKGROUND', (col, 0), (col, -1), colors.whitesmoke))

        if row == 0 and date:
            return date.strftime("%d\n{0}".format(date.strftime("%a")[0]))
        if col == 0 and issue:
            return "{0} - {1}".format(issue, issues_data[issue].fields.summary)
        if date and issue:
            task_total = sum(map(lambda w: w['spent'],
                                 filter(lambda w: w['issue'].key == issue,
                                        date_worklogs[date])))
            total_spent += task_total
            return "{:.1f}".format(task_total) if task_total else ""
        return ""

    dates = get_dates_in_range(from_date, to_date)
    data = [
        [
            cell_value(col, row, date, issue)
            for col, date in enumerate([None] + dates)
        ]
        for row, issue in enumerate([None] + list(issue_worklogs.keys()))
    ]

    register_fonts()
    doc = SimpleDocTemplate('%s.pdf' % assignee, pagesize=landscape(letter))

    elements = []

    stylesheet = getSampleStyleSheet()
    p = Paragraph('''
    <para align=center spacea=30>
        <font size=15>Jira Tasks Report ({0}-{1})</font>
    </para>'''.format(
        from_date.strftime(DATE_FORMAT),
        to_date.strftime(DATE_FORMAT)), stylesheet["BodyText"])
    elements.append(p)

    cw = [None] + [0.2*inch] * (len(data[0]) - 1)
    t = Table(data, style=ts, colWidths=cw)
    elements.append(t)

    p = Paragraph('''
    <para align=center spaceb=15>
        <font size=10>Total Hours: {:.2f}</font>
    </para>'''.format(total_spent), stylesheet["BodyText"])
    elements.append(p)

    doc.build(elements)
    
    return doc
    

def get_dates_in_range(from_date, to_date):
    dates = []
    current_date = from_date
    while True:
        dates.append(current_date)
        if current_date >= to_date:
            break
        current_date += timedelta(days=1)
    return dates


def register_fonts():
    pdfmetrics.registerFont(
        TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
               'UTF-8'))
    pdfmetrics.registerFont(
        TTFont('DejaVuSans-Bold',
               '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
               'UTF-8'))


@app.route("/worklog/<assignee>")
def worklog(assignee):
    get_worklog(assignee)
    return send_file('../%s.pdf' % assignee)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
