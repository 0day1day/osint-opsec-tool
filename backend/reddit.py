#!/usr/bin/python

import urllib2

import opsecHeader


def write_latest_post(author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink):
    sql = 'INSERT INTO reddit (author, body, link_id, comment_id, link_title, subreddit, epoch_time, permalink) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    opsecHeader.cur.execute(sql, (author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink))
    opsecHeader.db.commit()


def get_users():
    users = []
    sql = "SELECT author FROM reddit_users"
    opsecHeader.cur.execute(sql)
    for row in opsecHeader.cur.fetchall():
        users.append(row[0])
    return users


def get_latest_user_epoch(user):
    sql = "SELECT MAX(epoch_time) FROM reddit WHERE author = %s"
    opsecHeader.cur.execute(sql, (user))
    for row in opsecHeader.cur.fetchall():
        result = row[0]
    if result is None:
        result = 0
    return result


def get_user_comments(user):
    #http://www.reddit.com/dev/api

    user = urllib2.quote(user)

    reddit_query_string = 'http://www.reddit.com/user/' + user + '/overview.json'
    opsecHeader.query_website_json("reddit", reddit_query_string, opsecHeader.reddit_api_key)
    opsecHeader.write_last_checked_time('reddit')

    reddit_results = opsecHeader.read_results_json('reddit')
    try:
        reddit_all_results = reddit_results['data']['children']
    except KeyError:
        reddit_all_results = None
    epoch_time_existing = get_latest_user_epoch(user)

    if not reddit_all_results:
        print "No results."
    else:
        for i in reddit_all_results:
            epoch_time_found = str((i['data']['created_utc'])).encode('utf-8')[:-2]
            if int(epoch_time_found) > int(epoch_time_existing):
                try:
                    link_id = (i['data']['link_id']).encode('utf-8')[3:]
                except KeyError:
                    link_id = ''
                comment_id = (i['data']['id']).encode('utf-8')
                author = (i['data']['author']).encode('utf-8')
                try:
                    body = (i['data']['body']).encode('utf-8')
                except KeyError:
                    body = ''
                try:
                    link_title = (i['data']['link_title']).encode('utf-8')
                except KeyError:
                    link_title = ''
                subreddit = (i['data']['subreddit']).encode('utf-8')
                permalink = 'http://www.reddit.com/r/' + subreddit + '/comments/' + link_id + '/' + urllib2.quote(link_title) + '/' + comment_id
                write_latest_post(author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink)

                keywords = opsecHeader.get_user_keywords(author, 'reddit')
                for keyword in keywords:
                    if keyword in body:
                        opsecHeader.send_email(keyword, "Reddit", author)
