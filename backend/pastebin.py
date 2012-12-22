#!/usr/bin/python

# This script is a modified version of the "scrapePastebinMySQL.py" script from
# AndrewMohawk.com's PasteLert v2
#
# ---- EXTRACTED FROM ORIGINAL HEADER ----
# Parts stolen from @shellguardians pastebin.py script - Thanks!
# Do whatever you want with it -shrug-
# Andrew MacPherson
# @andrewmohawk
# http://www.andrewmohawk.com/
# ----- END EXTRACTED HEADER ----

import re
import random
import sys
import time
import urllib2

import opsecHeader

paste_ids_found = []
paste_max_size = 1000


def add_paste(title, paste_id, paste):
    keywords = opsecHeader.get_user_keywords('all', 'pastebin')
    for keyword in keywords:
        if keyword in paste:
            now = int(time.mktime(time.localtime()))
            sql = "INSERT INTO `pastebin` (`epoch_time`, `title`, `paste`, `pasteID`, `keyword`) VALUES (%s, %s, %s, %s, %s)"
            try:
                if(opsecHeader.cur.execute(sql, (now, title, paste, paste_id, keyword))):
                    opsecHeader.db.commit()
                    print "[+] Added."
            except:
                print '''[!] DB Problem (paste_id:%s) NOT inserted''' % (paste_id)
                print sys.exc_info()[0]
                return False
            opsecHeader.send_email(keyword, "Pastebin")


def get_pastes():
    global paste_ids_found, paste_max_size

    if(len(paste_ids_found) >= (paste_max_size * 2)):
        print "[-] cleaning list"
        for i in range(0, len(paste_ids_found) - (paste_max_size)):
            paste_ids_found.pop(0)
    print "[-] Pulling archive list..."
    try:
        page = urllib2.urlopen("http://www.pastebin.com/archive.php").read()
        regex = re.compile('<td><img src="/i/t.gif" .*?<a href="/(.*?)">(.*?)</a></td>.*?<td>(.*?)</td>', re.S)
        pastes = regex.findall(page)
        for i in pastes:
            paste_id = i[0]
            paste_title = i[1]
            fetch_attempt = 0
            opsecHeader.write_last_checked_time('pastebin')
            if(paste_id not in paste_ids_found):
                print "[-] New paste(", paste_id, ")"
                paste_ids_found.append(paste_id)
                print len(paste_ids_found)
                paste_page = ''
                while (paste_page == ''):
                    print "[+] Pulling Raw paste"
                    sock = urllib2.urlopen("http://pastebin.com/raw.php?i=" + paste_id)
                    paste_page = sock.read()
                    encoding = sock.headers['Content-type'].split('charset=')[1]  # iso-8859-1
                    try:
                        paste_page = paste_page.decode(encoding).encode('utf-8')
                        if(paste_page == ''):
                            paste_page = 'empty paste from http://pastebin.com/raw.php?i=' + paste_id
                        if "requesting a little bit too much" in paste_page:
                            paste_page = ''
                            print "[-] hitting pastebin too quickly, sleeping for 2 seconds and trying again.."
                            time.sleep(2)
                    except:
                        print "[!] couldnt decode page to utf-8"
                    print "[-] Sleeping for 1 second"
                    time.sleep(1)
                    fetch_attempt = fetch_attempt + 1
                    if(fetch_attempt > 1):
                        print "[+] Couldnt fetch " + "http://pastebin.com/raw.php?i=" + paste_id + " after 2 tries"
                        paste_page = '  '
                add_paste(paste_title, paste_id, paste_page)
            else:
                print "[-] Already seen ", paste_id
        sleep_time = random.randint(15, 45)
        print "[-] sleeping for", sleep_time, "seconds.."
        time.sleep(sleep_time)
        return 1
    except IOError:
        print "[!] Error fetching list of pastes, sleeping for 10 seconds and trying again"
        time.sleep(10)
        return 0


def main():
    while True:
        get_pastes()


if __name__ == "__main__":
    sys.exit(main())
