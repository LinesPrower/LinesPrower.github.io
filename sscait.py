# encoding:utf8
'''
@author: linesprower
'''

import io, re, os, json
import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/34.0.1847.116 Chrome/34.0.1847.116 Safari/537.36'


def load_page():
    url = 'http://sscaitournament.com/index.php?action=scoresCompetitive'
    t = requests.get(url, headers={'User-Agent': USER_AGENT})
    s = t.text
    with io.open('results.html', 'wt', encoding='utf8') as f:
        f.write(s)

def connect():
    return sqlite3.connect('sscait.db3')

TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<title>SSCAIT 2020/21 Crosstable</title>
<style type="text/css">
.c20 {background-color:#3fff3f;}
.c10 {background-color:#7fff7f;}
.c11 {background-color:#ffff00;}
.c01 {background-color:#ff7f7f;}
.c02 {background-color:#ff3f3f;}
.upcoming {background-color:#7f7fff;}
.upcoming0 {background-color:#0f0fff;}
.cself {background-color:#7f7f7f;}
.noqual {background-color:#cfcfcf;}
table { border-collapse:collapse; border:1px solid gray; }
td { border:1px solid gray; }
</style></head>
<body style="font-family:Ubuntu,Verdana; font-size: 12px;">
<p>%d/%d games played.
%s
</body>
</html>'''

def make_table():
    with io.open('results.html', encoding='utf8') as f:
        s = f.read()
    soup = BeautifulSoup(s, "lxml")

    up_list = []
    up_div = soup.find('div', id='upcomingMatchesWrapper')
    for t in up_div.find_all('span'):
        if 'vs.' in t.string:
            up_list.append(tuple(t.string.split(' vs. ')))

    upcoming0 = ', '.join('%s vs. %s' % t for t in up_list)
    upcoming = {t : i for i, t in enumerate(up_list)}
    upcoming.update({(b, a) : n for (a, b), n in upcoming.items()})


    def get_info(t):
        return (''.join(t.td.strings), t.find('span', class_='invisible').string)

#    bots_table = soup.find('table', id='bot_list').tbody
#    bots = []
#    for t in bots_table.find_all('tr'):
#        b = get_info(t)
#        if b not in bots:
#            bots.append(b)
#    print(bots)
#    return

    bots = [('Iron bot', 'Terran'), ('Ecgberht', 'Terran'), ('NLPRbot', 'Zerg'), ('PurpleWave', 'Protoss'), ('WillyT', 'Terran'),
            ('Steamhammer', 'Zerg'), ('Florian Richoux', 'Protoss'), ('Dragon', 'Terran'), ('ICELab', 'Terran'), ('Monster', 'Zerg'),
            ('Tomas Vajda', 'Protoss'), ('Dave Churchill', 'Random'), ('BetaStar', 'Protoss'), ('Hao Pan', 'Terran'), ('krasi0P', 'Protoss'),
            ('Arrakhammer', 'Zerg'), ('MegaBot2017', 'Protoss'), ('XIAOYICOG2019', 'Terran'), ('KasoBot', 'Terran'), ('Stardust', 'Protoss'),
            ('CUBOT', 'Zerg'), ('BananaBrain', 'Protoss'), ('MadMixP', 'Protoss'), ('TyrProtoss', 'Protoss'), ('Jakub Trancik', 'Protoss'),
            ('Martin Rooijackers', 'Terran'), ('Sijia Xu', 'Zerg'), ('NiteKatT', 'Terran'), ('Matej Istenik', 'Terran'), ('Proxy', 'Zerg'),
            ('Tomas Cere', 'Protoss'), ('WuliBot', 'Protoss'), ('NuiBot', 'Zerg'), ('Marian Devecka', 'Zerg'), ('Microwave', 'Zerg'),
            ('AILien', 'Zerg'), ('McRaveZ', 'Zerg'), ('Marine Hell', 'Terran'), ('Yuanheng Zhu', 'Protoss'), ('Simplicity', 'Zerg'),
            ('Bryan Weber', 'Zerg'), ('Flash', 'Protoss'), ('EggBot', 'Protoss'), ('Soeren Klett', 'Terran'), ('Slater', 'Protoss'),
            ('Andrew Smith', 'Protoss'), ('Aurelien Lermant', 'Zerg'), ('ZurZurZur', 'Zerg'), ('KaonBot', 'Terran'), ('Andrey Kurdiumov', 'Random'),
            ('Lukas Moravec', 'Protoss'), ('StyxZ', 'Zerg'), ('JumpyDoggoBot', 'Zerg'), ('Junkbot', 'Terran'), ('legacy', 'Random'), ('Chris Coxe', 'Zerg')]

    races = { b : r for b, r in bots }
    bots, _ = zip(*bots)
    bots = list(bots)

    #print(bots)

    matches = { b1 : { b2 : (0, 0) for b2 in bots } for b1 in bots }
    stats = { b1 : (0, 0) for b1 in bots }

    def add_bot(bname):
        x = { }
        for k, v in matches.items():
            x[k] = (0, 0)
            v[bname] = (0, 0)
        x[bname] = (0, 0)
        matches[bname] = x
        stats[bname] = (0, 0)
        bots.append(bname)
        races[bname] = '?'

    reslist = soup.find('table', id='resultlist')

    con = connect()
    games = {}
    for p1, p2, res, ts in con.execute('select * from games'):
        games[ts] = (p1, p2, int(res))

    n_games = 0
    for entry in reslist.find_all('tr'):
        def extract(x):
            if x.string:
                return x.string
            return x.get_text()
        data = [extract(x) for x in entry.find_all('td')]
        if data[0] == 'Bot 1':
            continue
        #print(data)
        b1 = re.sub(r'\s*\(.*\)', '', data[0])
        b2 = re.sub(r'\s*\(.*\)', '', data[1])
        game_res = int(data[2].split()[1])
        ts = data[4]
        if not ts in games:
            games[ts] = (b1, b2, game_res)
            print('Added game: ', games[ts])
            con.execute('insert into games values (?, ?, ?, ?)', (b1, b2, game_res, ts))

    con.commit()

    for b1, b2, res in games.values():
        if res == 2:
            b1, b2 = b2, b1

        #if b1 not in matches:
        #    add_bot(b1)
        #if b2 not in matches:
        #    add_bot(b2)

        a, b = matches[b1][b2]
        a += 1
        matches[b1][b2] = a, b
        a, b = matches[b2][b1]
        b += 1
        matches[b2][b1] = a, b

        a, b = stats[b1]
        a += 1
        stats[b1] = a, b

        a, b = stats[b2]
        b += 1
        stats[b2] = a, b

        n_games += 1


    def make_cell(idx, idx2, b1, b2):
        content = '&nbsp;'
        cl = 'none' if idx2 <= 18 else 'noqual'
        title = ''
        if b2 == '#':
            if idx == 0:
                content = '#'
            else:
                content = str(idx)
        elif b2 == '$':
            if idx == 0:
                content = 'W-L (%Wins)'
            else:
                w, l = stats[b1]
                if w + l > 0:
                    content = '%d-%d (%.1f%%)' % (w, l, 100 * w / (w + l))
                else:
                    content = '0-0'
        elif not b1 or not b2:
            if b1:
                content = '%s&nbsp;(%s)' % (b1, races[b1][0])
            elif b2:
                content = b2[:3]
                title = b2
            else:
                content = 'Player'
        else:
            if b1 == b2:
                cl = 'cself'
                title = '-'
            else:
                title = '%s - %s' % (b1, b2)
            a, b = matches[b1][b2]
            if a + b > 0:
                cl = 'c%d%d' % (a, b)
                content = '%d/%d' % (a, b)
            if (b1, b2) in upcoming:
                n = upcoming[(b1, b2)]
                cl = 'upcoming0' if n <= 2 else 'upcoming'
                if n == 1:
                    title += ' (upcoming in 1 game)'
                else:
                    title += ' (upcoming in %d games)' % n if n else ' (in progress)'
        # content = content.replace(' ', '&nbsp')
        return '<td class="%s" title="%s">%s</td>' % (cl, title, content)

    def get_winrate(bot):
        w, l = stats[bot]
        return (-w / (w + l) if w + l > 0 else 0, -w, bot)

    bots = sorted(bots, key=get_winrate)

    table = '\n'.join('<tr class="%s">%s</tr>' % ('qual' if i <= 16 else 'noqual',
                                                  ''.join(make_cell(i, i2, b1, b2) for i2, b2 in enumerate(['#', '', '$'] + bots)))
                      for i, b1 in enumerate([''] + bots))
    table = '<table>%s</table>' % table
    if upcoming0:
        table = '<p>Upcoming games: %s</p>\n%s' % (upcoming0, table)
    html = TEMPLATE % (n_games, 3080, table)
    outfile = 'sscait20.html'
    #outfile = 'C:/Projects/stuff/purplepie.bitbucket.org/sscait18.html'
    with io.open(outfile, 'wt') as f:
        f.write(html)
    print(n_games)


def get_games_info(cnt, page):
    url = 'https://sscaitournament.com/api/games.php?count=%d&future=False&page=%d' % (cnt, page)
    t = requests.get(url, headers={'User-Agent': USER_AGENT})
    s = t.text
    with io.open('games%d.json' % page, 'wt', encoding='utf8') as f:
        f.write(s)
    json = t.json()
    print(len(json))

def import_games(fname):
    with io.open(fname, 'rt', encoding='utf8') as f:
        data = json.loads(f.read())
    tz = datetime.timezone(datetime.timedelta(hours=1))

    con = connect()
    games = {}
    for p1, p2, res, ts in con.execute('select * from games'):
        games[ts] = (p1, p2, int(res))

    n_games = 0
    for x in data:

        b1 = x['host']
        b2 = x['guest']
        game_res = int(x['result'])
        ts = datetime.datetime.fromtimestamp(int(x['timestamp']), tz).strftime('%Y-%m-%d %H:%M:%S')
        if not ts in games:
            games[ts] = (b1, b2, game_res)
            print('Added game: %s' % ts)
            con.execute('insert into games values (?, ?, ?, ?)', (b1, b2, game_res, ts))
            n_games += 1

    print('Added %d games' % n_games)
    con.commit()

def main():
    #for i in range(1, 5):
    #	get_games_info(1180, i)
    #for i in range(1, 6):
    #    import_games('games%d.json' % i)
    load_page()
    make_table()
    # gen_strings()
    # get_stats()


if __name__ == '__main__':
    main()
