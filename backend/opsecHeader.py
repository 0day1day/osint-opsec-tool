#!/usr/bin/python

import gzip
import json
import MySQLdb
import os
import smtplib
import socket
import sys
import time
import urllib2
from ConfigParser import SafeConfigParser
from StringIO import StringIO

############## READ CONFIG ################
if __name__ == '__main__':
    path = os.path.split(sys.argv[0])[0]
else:
    path = os.path.split(__file__)[0]

parser = SafeConfigParser()
parser.read(os.path.join(path, 'config.ini'))

receiver_email = parser.get('email', 'receiver_email').replace("'", "")
sender_email = parser.get('email', 'sender_email').replace("'", "")
email_pw = parser.get('email', 'email_pw').replace("'", "")
reddit_api_key = parser.get('reddit', 'reddit_api_key').replace("'", "")
stackexchange_api_key = parser.get('stackexchange', 'stackexchange_api_key').replace("'", "")

############# CONNECT TO DB ###############

db_host = parser.get('database', 'db_host').replace("'", "")
db_name = parser.get('database', 'db_name').replace("'", "")
db_user = parser.get('database', 'db_user').replace("'", "")
db_pw = parser.get('database', 'db_pw').replace("'", "")

db = MySQLdb.connect(host=db_host, db=db_name, user=db_user, passwd=db_pw)
cur = db.cursor()

################ METHODS ##################


def write_last_checked_time(source):
    now = int(time.mktime(time.localtime()))
    sql = "UPDATE last_checked SET last_checked = %s WHERE source = %s"
    cur.execute(sql, (now, source))
    db.commit()


def write_temp_results(website, results):
    working_file = '/tmp/OPSEC.' + website
    file_handle = open(working_file, 'w')
    file_handle.write(results)
    file_handle.close()


def read_results_json(website):
    try:
        file_handle = open('/tmp/OPSEC.' + website, 'r')
        return json.load(file_handle)
    except IOError:
        print "Error opening file"
        return None


def query_website_json(website, query, user_agent='Python-urllib/2.7'):
    print "\nQuerying " + website + "..."
    print query

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', user_agent)]

    try:
        url_results = opener.open(query)

        if url_results.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(url_results.read())
            file_handle = gzip.GzipFile(fileobj=buf)
            results = file_handle.read()
        else:
            results = url_results.read()

        print results
        url_results.close()

        write_temp_results(website, results)
    except urllib2.HTTPError:
        print "Error fetching JSON"


def send_email(keyword, source, user=None):
    domain = str(socket.gethostname())
    subject = 'OSINT OPSEC Tool - Keyword Detected'
    body = "'" + keyword + "'" + " has been detected on " + source
    if user is not None:
        body += " for user '" + user + "'"
    body += ".\n\n https://" + domain
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
        % (sender_email, receiver_email, subject, body))
    smtp = smtplib.SMTP('localhost')
    smtp.login(sender_email, email_pw)
    smtp.sendmail(sender_email, [receiver_email], msg)
    smtp.quit()


def get_user_keywords(user, source):
    keywords = []
    sql = "SELECT keyword FROM keywords WHERE user = %s AND source = %s"
    cur.execute(sql, (user, source))
    for row in cur.fetchall():
        keywords.append(row[0])
    return keywords
