import re
import os
import sys
import urllib
import urllib2
import getopt
import cookielib
from BeautifulSoup import BeautifulSoup
from itertools import chain

MB_TO_GB = 0.0009765625
verbose = True
user = ''
password = ''


def getLogin():
    ''' Logs in to what.cd and gets a cookie
        opener is returned and should be used to open other pages '''

    vPrint('Logging you in as ' + user + '.')
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    login_data = urllib.urlencode({'username': user,
                                   'password': password})
    check = opener.open('https://what.cd/login.php', login_data)
    soup = BeautifulSoup(check.read())
    warning = soup.find('span', 'warning')
    if warning:
        exit('Username or password is incorrect.')

    vPrint('Login successful.')

    return opener


def getSize(line):
    ''' Gets the size of all the torrents of a certain release '''
    return re.sub('<.*', '', re.sub('.*">', '', line))


def getContent(url, login):
    ''' Gets the content of the url '''
    handler = login.open(url)
    line = '0'
    content = list()
    size = 0
    while line != '':
        line = handler.readline()
        if 'href' in line and '>DL</a>' in line:
            content.append('http://what.cd/' + getUrl(line)[:-1])
        if 'nobr' in line and 'B</td>' in line:
            tmp = getSize(line)
            tmp = tmp.split()
            if tmp[1] == 'MB':
                size += float(tmp[0]) * MB_TO_GB
            else:
                size += float(tmp[0])

    return content, size


def getUrl(line):
    ''' Trims lines for the torrent url '''
    return re.sub('&amp;', '&', re.sub('".*', '', re.sub('.*href="', '', line)))


def freeleechUrl(n):
    ''' Generates freeleech url '''
    return 'http://what.cd/torrents.php?page=' + str(n) + '&freetorrent=1'


def freeleechTorrents(login):
    ''' Gets all of the freeleeech torrents and returns them in a list '''
    torrents = list()
    size = 0
    for i in range(1, 4):
        t, tSize = getContent(freeleechUrl(i), login)
        torrents.append(t)
        size += tSize

    return list(chain.from_iterable(torrents)), size


def genFilename(filename):
    ''' Generates a filename from the old one '''
    count = 1
    ext = '.torrent'
    name = re.sub(ext, '', filename)
    while os.path.isfile(filename):
        filename = name + ' (' + str(count) + ')' + ext
        count += 1

    return filename


def download(torrent, login):
    ''' Downloads the torrent to the current folder '''
    handler = login.open(torrent)
    filename = re.sub('.*="', '', handler.headers['content-disposition'])[:-1]
    if os.path.isfile(filename):
        filename = genFilename(filename)
    f = open(filename, 'wb')
    f.write(handler.read())
    f.close()


def vPrint(instr):
    ''' Verbose Print '''
    if verbose:
        print instr


def usage():
    vPrint("==================================================")
    vPrint("Usage: freeleech.py [OPTION]")
    vPrint("What.CD freeleech downloader")
    vPrint("")
    vPrint(" -l/--login user:password, override default login")
    vPrint(" -q/--quiet go silent")
    vPrint(" -h/--help this message")
    vPrint("==================================================")
    sys.exit(' ')


def run():
    login = getLogin()
    torrents, size = freeleechTorrents(login)
    count = 0

    print str(len(torrents)), 'torrents available for download'
    print'total size:', size, 'GB\n'

    c = raw_input("Proceed? y/n\n")

    if c == 'y' or c == 'Y':
        if verbose:
            print '\nStarting downloads.'
            total = len(torrents)
        for i in torrents:
            download(i, login)
            if verbose:
                count += 1
                print count, 'of', total


def main():
    global verbose
    global user
    global password

    try:
        opts, args = getopt.gnu_getopt(sys.argv, "l:qh", \
                                        ["login=", "quiet", "help"])

    except getopt.GetoptError:
        usage()

    for o, a in opts:
        if o in ('-q', '--quiet'):
            verbose = False
        elif o in ('-h', '--help'):
            usage()

        if o in ('-l', '--login'):
            if ':' not in a:
                usage()
            user, password = a.split(':')

    run()


if __name__ == "__main__":
    main()
