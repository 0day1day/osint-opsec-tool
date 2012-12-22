#!/usr/bin/python

import calendar
import time
import urllib2

import opsecHeader


def write_latest_post(name, user_id, message, profile_picture, updated_time, keyword, epoch_time):
    sql = "INSERT INTO facebook (name, user_id, message, profile_picture, updated_time, keyword, epoch_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    opsecHeader.cur.execute(sql, (name, user_id, message, profile_picture, updated_time, keyword, epoch_time))
    opsecHeader.db.commit()


def get_latest_post_time():
    result = '0'
    opsecHeader.cur.execute("SELECT MAX(epoch_time) FROM `facebook`")
    for row in opsecHeader.cur.fetchall():
        result = row[0]
    return result


def get_profile_picture(user_id):
    profile_picture_string = 'https://graph.facebook.com/' + user_id + '/picture'
    url_result = urllib2.urlopen(profile_picture_string)
    result = url_result.geturl().encode('utf-8')
    url_result.close()
    return result


def search_facebook(raw_keyword):
    opsecHeader.write_last_checked_time('facebook')
    keyword = urllib2.quote(raw_keyword)
    # See https://developers.facebook.com/docs/reference/api/
    #
    # Arguments:
    # q = keyword we are searching for
    # type = kind of object we are searching for e.g post
    #
    # Returns:
    # name; id (facebook.com/id for their profile)

    facebook_latest_epoch = get_latest_post_time()
    facebook_query_string = 'https://graph.facebook.com/search?q=' + keyword + '&type=post'
    opsecHeader.query_website_json("facebook", facebook_query_string)

    print "Parsing Facebook data..."

    facebook_results = opsecHeader.read_results_json('facebook')
    facebook_all_results = facebook_results['data']

    if facebook_all_results:
        for i in facebook_all_results:
            if 'message' in i:
                message = i['message'].encode('utf-8')
                name = (i['from']['name']).encode('utf-8')
                user_id = (i['from']['id']).encode('utf-8')
                updated_time = (i['updated_time']).encode('utf-8')
                epoch_time = calendar.timegm((time.strptime(updated_time, '%Y-%m-%dT%H:%M:%S+0000')))

                if int(epoch_time) > int(facebook_latest_epoch):
                    profile_picture = get_profile_picture(user_id)
                    write_latest_post(name, user_id, message, profile_picture, updated_time, keyword, epoch_time)
                    opsecHeader.send_email(keyword, "Facebook")
                    print "Updated Time: " + updated_time
                else:
                    print "Post too old."
