import requests
from bs4 import BeautifulSoup

HDRS = {
    'user-agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                + '(KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36')
}

def fossbytes_feed():
    resp = requests.get('https://fossbytes.com/feed/atom', headers=HDRS).content
    soup = BeautifulSoup(resp, 'lxml')
    articles = soup.select('entry')
    
    return [article.select_one('link').get('href') for article in articles]

def xdadev_feed():
    "only page 1. around 16 posts"

    resp = requests.get('https://www.xda-developers.com/', headers=HDRS)
    soup = BeautifulSoup(resp.content, 'lxml')
    feeds = []
    featured_feeds = soup.select('.desktop-featured-header .layout_post_1')
    feeds.extend([feed.select_one('a').get('href') for feed in featured_feeds])
    remaining_feeds = soup.select('.layout_post_2 .item_content')
    feeds.extend([feed.select_one('a').get('href') for feed in remaining_feeds])

    return feeds

def torrentfreak_feed():
    
    resp = requests.get('https://torrentfreak.com', headers=HDRS)
    soup = BeautifulSoup(resp.content, 'lxml')
    top_hero = soup.select_one('section a.hero')
    if not top_hero: return []
    articles = [top_hero.get('href')]
    rem_articles = soup.select('article.preview-article a')
    for article in rem_articles:
        articles.append(article.get('href'))
    return articles

def jsonToXML(url):
    r = requests.get('https://www.convertjson.com/cgi-bin/url-to-json.php?callback=loadDataAndRun&url=' + url)
    return r.json()

def hn_get_top_stories() -> list:
    return requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()

def hn_get_type(u_id):
    return requests.get(f'https://hacker-news.firebaseio.com/v0/item/{u_id}.json').json()

def hn_get_item(item_id):
    return hn_get_type(item_id)

def hn_get_story_comment(c_id):
    return hn_get_type(c_id)

def hn_get_direct_comments_only(s_id):
    try:
        children = hn_get_item(s_id)['kids']
    except KeyError:
        return []
    return [hn_get_story_comment(child) for child in children]

def recursive_comments(c_id):
    comment = hn_get_type(c_id)
    if 'kids' in comment:
        for desc_id in comment['kids']:
            return [desc_id] + recursive_comments(desc_id)
    else:
        return [comment['id']]

def hn_get_all_story_comments(s_id):
    comment_ids = []
    try:
        children = hn_get_item(s_id)['kids']
    except KeyError:
        return []
    for descendants_id in children:
        print(descendants_id)
        comment_ids.append(recursive_comments(descendants_id))
    # for comment in hn_get_direct_comments_only(s_id):
        # pass
    return comment_ids

def cpad(text: str, width: int, filler: str, allow_partial_fill : bool = True):
    if len(text) >= width:
        return text

    width_available = width - len(text)
    multiplier = width_available // len(filler)
    part = ''
    pad = filler * (multiplier // 2)
    if allow_partial_fill:
        part = filler[:multiplier % 2]
    pad += part
    
    return pad + text + pad


if __name__ == '__main__':
    HDRS = {}
    # print(fossbytes_feed())
    # print(xdadev_feed())
    # print(torrentfreak_feed())
    import os
    import logging
    from telegram import Telegram
    from datetime import datetime, timezone

    # logging.basicConfig(level=10)
    # logger = logging.getLogger(__name__)

    # print(requests.get('https://hacker-news.firebaseio.com/v0/askstories.json').json())
    # print(requests.get('https://hacker-news.firebaseio.com/v0/showstories.json').json())
    # print(requests.get('https://hacker-news.firebaseio.com/v0/jobstories.json').json())
    # print(hn_get_item('27037870')) # Ask HN
    # print(hn_get_item('27034904')) # Show HN
    # print(hn_get_item('27039789')) # job
    # resp = requests.get(
    #             url='http://51.158.118.221:8081/torrentfreak/v1/articles/posts/',
    #             params={'per_page': 15, 'page': 1},
    #             headers={'User-Agent': 'Universal/2.0 (Android)'})
    import sys; sys.exit()

    api_key = os.environ['BOTAPIKEY']

    with Telegram('-1001162454492', api_key, sendWithoutSound=False) as ch:
        for s_id in hn_get_top_stories()[:5]:
            story = hn_get_item(s_id)
            posted_on = datetime.fromtimestamp(story['time'], tz=timezone.utc)

            url = story.get('url', '')
            # HN seems to pick site(eTLD+1) with special hnadling for sites like twitter
            try:
                # Show HN, job
                hostname = url.split('/')[2]
            except IndexError:
                # this handles lack of scheme, ASK HN(no url)
                hostname = url.split('/')[0]

            max_char_per_line = 64
            hostname = cpad(hostname, max_char_per_line, ' · ')

            ch.sendText(
                Telegram.bold(story['title'] + '\n', escape=True)
                + Telegram.captionedUrl(
                    caption=Telegram.escape(
                        f"▲ {story['score']} "
                        + "| " + posted_on.strftime("%H:%M %b %d '%y")
                        + f"| {story['descendants']} comments\n\n"
                        # + '·' * 118 + "\n\n"
                        ),
                    url=f"https://news.ycombinator.com/item?id={story['id']}",
                )
                + Telegram.captionedUrl(
                    caption=Telegram.bold(hostname, escape=True), url=url,
                )
            )
            break

    # # https://news.ycombinator.com/lists # check this too
    # print(hn_get_direct_comments_only(24979141))
    # print(hn_get_all_story_comments(24998370))

    '''
    t.me/iv?url=...&rhash=...

    !!!! fossbytes already has slightly better instant view page
    !!!! HN is basically nested tables which seems impossible to replace with anything
        and preserve left indent child comments.
        Wanted to not include child comments only the parents using api but cannot
        most prob. the problem is cannot embed MIME type application/json in an iframe only text/html.

    fossbytes
    -1001183664935
    t.me/iv?url={url}&rhash=8a2290abc57029

    xda-developers
    -1001480837415
    t.me/iv?url={url}/&rhash=7931f7826d605e

    torrentfreak
    -1001333440900
    t.me/iv?url={url}/&rhash=b812ff3d6d522e

    //table//tr[contains(@class, "athing comtr")]//td/img/@width
    //table//tr[has-class("comtr")]//td/img/@width

    //td[@class="default"]/preceding-sibling::td[2]/img/@width

    '''
    # @set_attr(para-text, $pargraph): $body
    # $tables: $body//table/tr[has-class("comtr")]//table

    # @map( $tables) {
    #     $pargraph:  $@//span[has-class("commtext")]
    #     $width:     $@//img/@width
    #     @replace("\\d+", $width):       $body/@style
    #     @replace("0", ""):              $body/@style
    #     @append(<p>, "style", @style):  $body
    # }

    # @set_attr(style, "padding-left: .5rem"): $body//*[@class="hn-ct"]
    # @set_attr(style, "margin-left: .5rem"): $body//*[@class="hn-cl"]//*[@class="hn-cl"]
    # @remove: $body//table
