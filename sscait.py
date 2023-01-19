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
<title>SSCAIT 2022/23 Crosstable</title>
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
td { border:1px solid gray; text-align: center; }
</style></head>
<body style="font-family:Ubuntu,Verdana; font-size: 12px;">
<p>%d/%d games played. Disclaimer: this crosstable is unofficial and for information purposes only. Visit the <a href="https://sscaitournament.com">SSCAIT website</a> for official results.</p>
<p>Disclaimer 2: due to certain problems in the tournament's infrastructure, there are games where one of the bots does not start, resulting in an automatic loss.</p>
%s
</body>
</html>'''

def make_table(plain):
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
#    print(len(bots))
#    return

    bots = [('TyrProtoss', 'Protoss'), ('PurpleWave', 'Protoss'), ('BananaBrain', 'Protoss'), ('legacy', 'Random'), ('Junkbot', 'Terran'),
            ('MadMixP', 'Protoss'), ('WillyT', 'Terran'), ('Chris Coxe', 'Zerg'), ('krasi0', 'Terran'), ('Stardust', 'Protoss'),
            ('Iron bot', 'Terran'), ('Dragon', 'Terran'), ('BetaStar', 'Protoss'), ('Hao Pan', 'Terran'), ('Tomas Vajda', 'Protoss'),
            ('McRaveZ', 'Zerg'), ('KasoBot', 'Terran'), ('Monster', 'Zerg'), ('Pathos', 'Zerg'), ('ZurZurZur', 'Zerg'),
            ('ICELab', 'Terran'), ('XIAOYICOG2019', 'Terran'), ('Proxy', 'Zerg'), ('CUBOT', 'Zerg'), ('Zerg Hell', 'Zerg'),
            ('Simplicity', 'Zerg'), ('Infested Artosis', 'Zerg'), ('Steamhammer', 'Zerg'), ('WuliBot', 'Protoss'), ('AILien', 'Zerg'),
            ('Dave Churchill', 'Random'), ('Martin Rooijackers', 'Terran'), ('MegaBot2017', 'Protoss'), ('Ecgberht', 'Terran'),
            ('NLPRbot', 'Zerg'), ('KaonBot', 'Terran'), ('StyxZ2', 'Zerg'), ('Yuanheng Zhu', 'Protoss'), ('Lukas Moravec', 'Protoss'),
            ('Soeren Klett', 'Terran'), ('NuiBot', 'Zerg'), ('Marine Hell', 'Terran'), ('Andrew Smith', 'Protoss'), ('Matej Istenik', 'Terran'),
            ('DTD Bot', 'Protoss'), ('Florian Richoux', 'Protoss'), ('Arrakhammer', 'Zerg'), ('Sijia Xu', 'Zerg'), ('Boris', 'Zerg'),
            ('Jakub Trancik', 'Protoss'), ('Aurelien Lermant', 'Zerg'), ('JumpyDoggoBot', 'Zerg'), ('Microwave', 'Zerg'),
            ('insanitybot', 'Terran'), ('Flash', 'Protoss'), ('Bryan Weber', 'Zerg'), ('Tomas Cere', 'Protoss')]

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
    for p1, p2, res, ts, _ in con.execute('select * from games'):
        games[ts] = (p1, p2, int(res))

    n_games = 0
    for entry in reslist.find_all('tr'):
        def extract(x):
            refs = x.find_all('a', recursive=False)
            if refs and refs[-1].string == 'watch':
                return refs[-1]['href']
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
        link = data[5]
        if not ts in games:
            games[ts] = (b1, b2, game_res)
            print('Added game: ', games[ts])
            con.execute('insert into games values (?, ?, ?, ?, ?)', (b1, b2, game_res, ts, link))

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
            wins, loses = matches[b1][b2]

            if wins + loses > 0:
                cl = 'c%d%d' % (wins, loses)
                content = '%d:%d' % (wins, loses)

            if not plain:
                def icon(name):
                    return '<img src="%s" height=20 width=20 />' % name

                def use_icon(icon_name):
                    nonlocal content, title
                    content = icon(icon_name)
                    title += ', %d:%d' % (wins, loses)

                if b1 == 'Monster' and wins == 2:
                    use_icon('meat.svg')
                elif b1 == 'Monster' and loses == 2:
                    use_icon('knife.svg')
                elif b1 == 'Stardust' and wins == 2:
                    use_icon('mushroom.svg')
                elif b1 == 'Stardust' and loses == 2:
                    use_icon('cheese.svg')
                elif b1 == 'Hao Pan' and wins == 2:
                    use_icon('cheese.svg')
                elif b1 == 'Hao Pan' and loses == 2:
                    use_icon('shallow_pan.svg')
                elif b1 == 'PurpleWave' and wins == 2:
                    use_icon('purple_heart.svg')
                elif b1 == 'PurpleWave' and loses == 2:
                    use_icon('broken_heart.svg')
                elif b1 == 'BananaBrain' and wins == 2:
                    use_icon('banana.svg')
                elif b1 == 'BananaBrain' and loses == 2:
                    use_icon('brain.svg')
                elif b1 == 'Steamhammer' and wins == 2:
                    use_icon('hammer.svg')
                elif b1 == 'Dragon' and wins == 2:
                    use_icon('dragon.svg')
                elif b1 == 'McRaveZ' and wins == 2:
                    use_icon('mcrave_win.webp')
                elif b1 == 'McRaveZ' and loses == 2:
                    use_icon('mcrave_loss.webp')
                elif b1 == 'StyxZ' and loses == 2:
                    use_icon('bugs.png')
                elif b1 == 'MadMixP' and wins == 2:
                    use_icon('crazy.svg')
                elif b1 == 'MadMixP' and loses == 2:
                    use_icon('brainfuck.svg')
                elif b1 == 'EggBot' and wins == 2:
                    use_icon('egg.svg')
                elif b1 == 'EggBot' and loses == 2:
                    use_icon('omlette.svg')
                elif b1 == 'Ecgberht' and wins == 2:
                    use_icon('crown.svg')
                elif b1 == 'Tomas Vajda' and wins == 2:
                    use_icon('airplane.svg')
                elif b1 == 'Tomas Vajda' and loses == 2:
                    use_icon('boom.svg')
                elif b1 == 'Microwave' and wins == 2:
                    use_icon('microwave.png')
                elif b1 == 'Microwave' and loses == 2:
                    use_icon('boom.svg')
                elif b1 == 'Iron bot' and wins == 2:
                    use_icon('iron.png')
                elif b1 == 'krasi0' and wins == 2:
                    use_icon('linux.svg')
                elif b1 == 'krasi0' and loses == 2:
                    use_icon('windows.png')
                elif b1 == 'Andrew Smith' and wins == 2:
                    use_icon('skynet.png')
                elif b1 == 'Andrew Smith' and loses == 2:
                    use_icon('rubbish.svg')
                elif b1 == 'Chris Coxe' and wins == 2:
                    use_icon('stopwatch.svg')
                elif b1 == 'Aurelien Lermant' and wins == 2:
                    use_icon('dollar.svg')
                elif b1 == 'Junkbot' and wins == 2:
                    use_icon('rubbish.svg')
                elif b1 == 'CUBOT' and wins == 2:
                    use_icon('ice_cube.svg')
                elif b1 == 'NiteKatT' and wins == 2:
                    use_icon('black_cat.png')
                elif b1 == 'BetaStar' and wins == 2:
                    use_icon('milk.svg')
                elif b1 == 'WillyT' and wins == 2:
                    use_icon('pretzel.svg')
                elif b1 == 'XIAOYICOG2019' and wins == 2:
                    use_icon('mi.svg')
                elif b1 == 'JumpyDoggoBot' and wins == 2:
                    use_icon('dog.svg')
                elif b1 == 'JumpyDoggoBot' and loses == 2:
                    use_icon('hotdog.svg')
                elif b1 == 'Marian Devecka' and wins == 2:
                    use_icon('killer.png')
                elif b1 == 'Proxy' and wins == 2:
                    use_icon('microbe.svg')
                elif b1 == 'TyrProtoss' and wins == 2:
                    use_icon('cherries.svg')
                elif b1 == 'WuliBot' and wins == 2:
                    use_icon('watermelon.svg')
                elif b1 == 'ICELab' and wins == 2:
                    use_icon('ice_cream.svg')
                elif b1 == 'ICELab' and loses == 2:
                    use_icon('milk.svg')
                elif loses == 2:
                    use_icon('potato.png')
                elif wins == 1 and loses == 1:
                    content = icon('handshake.svg')
                    title += ', 1:1'

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
    if plain:
        table += '\n<p><a href="sscait22.html">Remastered edition</p>'
    else:
        table += '\n<p><a href="sscait22p.html">Plain version</p>'
    tot_games = len(bots) * (len(bots) - 1)
    html = TEMPLATE % (n_games, tot_games, table)
    outfile = 'sscait22p.html' if plain else 'sscait22.html'
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
        ts = datetime.datetime. fromtimestamp(int(x['timestamp']), tz).strftime('%Y-%m-%d %H:%M:%S')
        if not ts in games:
            games[ts] = (b1, b2, game_res)
            print('Added game: %s' % ts)
            con.execute('insert into games values (?, ?, ?, ?, ?)', (b1, b2, game_res, ts, None))
            n_games += 1

    print('Added %d games' % n_games)
    con.commit()

def check_duplicates():
    con = connect()
    data = list(con.execute('select p1, p2, game_result, time_stamp, rowid from games order by p1, p2, game_result, time_stamp'))
    old = None
    old_t = None
    old_id = None
    reps = []
    for entry in data:
        cur = tuple(entry[:2])
        ts = datetime.datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S')
        if cur == old:
            if (ts - old_t).total_seconds() < 90:
                print('Repeated game: %s %s' % (old_id, old))
                reps.append(old_id)
        old = cur
        old_t = ts
        old_id = entry[4]
    for dbid in reps:
        con.execute('delete from games where rowid = ?', (dbid,))
    con.commit()

def main():
    #for i in range(1, 5):
    #	get_games_info(1180, i)
    #for i in range(1, 6):
    #    import_games('games%d.json' % i)
    check_duplicates()
    load_page()
    make_table(False)
    make_table(True)
    # gen_strings()
    # get_stats()


if __name__ == '__main__':
    main()
