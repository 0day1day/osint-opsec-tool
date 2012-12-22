#!/usr/bin/python

import opsecHeader
import urllib2


def write_latest_wordpress(epoch_time, title, author, content, link, keyword):
    sql = "INSERT INTO wordpress (epoch_time, title, author, content, link, keyword) VALUES (%s, %s, %s, %s, %s, %s)"
    opsecHeader.cur.execute(sql, (epoch_time, title, author, content, link, keyword))
    opsecHeader.db.commit()


def get_latest_wordpress():
    result = '0'
    opsecHeader.cur.execute("SELECT epoch_time FROM `wordpress` ORDER BY epoch_time desc LIMIT 1")
    for row in opsecHeader.cur.fetchall():
        result = row[0]
    return result


def search_wordpress(raw_keyword):
    keyword = urllib2.quote(raw_keyword)
    opsecHeader.write_last_checked_time('wordpress')

    ############### WORDPRESS ##################
    #
    # See http://en.search.wordpress.com/?q=obama&s=date&f=json
    #
    # Arguments:
    # q = keyword to search for
    # s = sort by; we want date; not relevance
    # f = format; we want JSON

    wordpress_query_string = 'http://en.search.wordpress.com/?q=' + keyword + '&s=date&f=json'

    opsecHeader.query_website_json("wordpress", wordpress_query_string)

    wordpress_latest_epoch = get_latest_wordpress()
    wordpress_results = opsecHeader.read_results_json('wordpress')
    epoch_time = wordpress_results[0]['epoch_time']

    if str(wordpress_latest_epoch) == str(epoch_time):
        print "No new blog posts since last query."
    else:
        for i in wordpress_results:
            epoch_time = i['epoch_time']
            if int(wordpress_latest_epoch) < int(epoch_time):
                title = (i['title']).encode('utf-8')
                author = (i['author']).encode('utf-8')
                content = (i['content']).encode('utf-8')
                link = (i['link']).encode('utf-8')
                write_latest_wordpress(epoch_time, title, author, content, link, keyword)
                opsecHeader.send_email(keyword, "Wordpress")
