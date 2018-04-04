# Jira Timesheet Export

One of the trivial tasks in Jira without buying an additional plugin is the
export of a timesheet for particular user. The purpose of this script is to
allow you to export the timesheet for specific user time range, only using the
default Jira API.

# How to run the script?

- Clone this repository
- `docker build -t jira-timesheet-export .`
- `docker run -it -p 81:80 -v `pwd`:/code jira-timesheet-export python3 src/main.py `
- Provide input once required
- Browse to http://localhost:81/worklog/<assignee> where <assignee> is the name of the Jira worklog author you are interested in reporting on
