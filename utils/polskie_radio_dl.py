import sys
import requests
from bs4 import BeautifulSoup




# Downloader for Polskie radio audycje / podcasty

# Example url:
# https://podcasty.polskieradio.pl/trojka/audycje/strefa-rokendrola-wolna-od-angola,350

url = sys.argv[1].split("?")[0]
url0 = url.split(".pl")[1]
dir = sys.argv[2]


for pagenumber in range(1, 1000):
    r = requests.get(url + "?page=%d" % pagenumber)
    print("Page", pagenumber)
    if "Nie znaleziono odcinków" in r.text:
        print("Ostatnia strona.")
        break
    soup = BeautifulSoup(r.content, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(url0 + "/odcinek"):
            id = href.split(",")[-1]
            title = a.text.replace(" ", "_").replace("/", "_") + ".mp3"

            for nx in a.find_next_sibling().children:
                break

            date = nx.text
            d,m,y = date.split(".")
            date = ".".join([y,m,d])
            title = date + "--" + title

            u = "https://static.prsa.pl/%s.mp3" % id
            print("Downloading", title)
            print("Url:", u)

            r = requests.get(u).content

            open(dir + "/" + title, "wb").write(r)
