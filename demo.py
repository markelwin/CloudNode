from cloudnode import SwiftData, SwiftDataBackend, sd, RuntimeConfig
import dataclasses

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This demo creates a simple storage utility for scraping websites and constructing a search index to retrieve those.
# this demo requires installing beautifulsoup: pip install BeautifulSoup4   # parses html into searchable elements
# this demo requires installing selenium: pip install selenium              # operates a browser to interact with js
# this demo requires docker to be installed and running on your os: https://docs.docker.com/engine/install/
# This demo and its apis are expected to change: future updates will also use cloudnode app infrastructure additionally.

applet = "early"  # the name of the applet itself
index = "demo"    # an index is a silo'd search repository; i.e., WebPage index=demo and index=prod are different dbs

# Here we define the database class itself; this demo includes unnecessary fields to educate the developer here.
# We then list the set of urls we will load into the database and use a combination of Selenium and BeautifulSoup to
# download those URLs and process its HTML. Selenium is a browser replication system which interacts with web pages
# precisely as a user does manually through a browser. This is necessary to load modern html pages which had embedded
# javascript and ads, each of which are requested and downloaded by the browser after the raw html itself is downloaded.
# For all intents and purposes here these are only being used as fancy heavy download engines for the webpages.
# How the demo works: running a search database has more moving parts than simply writing files to disk; so this demo
# makes use of the flexibility of our SwiftData: first, the demo simply downloads the html, creates a WebPage object
# and then takes advantage of our SwiftData flexibility to simply write these objects to disk. From that point on we
# have the files downloaded and can cut out the slow downloading steps without ever needing to boot up a search engine.
# Users interact with these filesystem version exactly the same as the search api calls by setting the es=False flag in
# each call; and future updates will allow approximate per-field search capabilities into those data files, so that data
# management can happen on disk or in search nearly identically (the only different will be improved search capabilities
# using the full algorithm capabilities of search engine analyzers). This capabilities does not exist with other search.
# SwiftData is also built to be very user friendly with data-type by handling data conversions automatically, so that a
# user may set a timestamp field, e.g. using string forms or python datetimes, or geopoints e.g. in most common formats.
# As a user note: we recommend setting ids manually using a base64 from a unique value field on each data (for instance,
# the url of the website); base64 produces a lengthy unique string and is also reversable, which reduces a very common
# headache of initial users working with databases which is multiple runs adding the same data multiple times with
# different automatically generated ids; this method we describe allows robust "if id does not exist; process the data".
# Future iterations will make this id generation less technical but for now we want to leave this exposed to the user.
logger.info(f"Filestorage is using: {RuntimeConfig.directory_base_local}")
SwiftData.help()

########################################################################################################################
# five minute demo: defining problem statements and using local filestorage
########################################################################################################################


@dataclasses.dataclass
class WebPage(SwiftData):
    url: sd.string()                  # an exact string; facilitating exact matches only
    domain: sd.string()
    text: sd.string(analyze=True)     # a body of text; tokenized, analyzed and searchable
    html: sd.string(dont_index=True)  # a string stored in the engine but not intended for search
    labels: sd.string(list=True)      # a list of exact strings; matching one or all is possible
    now: sd.timestamp()               # a timestamp; searchable using windows of time
    geo: sd.geopoint(list=True)       # a list of gps defined spots; searchable via radius


pages = [
    "https://www.nytimes.com/2024/09/19/nyregion/cuomo-nursing-homes-covid.html",
    "https://www.nytimes.com/2024/09/19/nyregion/los-angeles-earthquakes-attitudes.html",
    "https://www.nytimes.com/2024/09/19/climate/us-methane-greenhouse-gas.html",
    "https://www.nytimes.com/2024/09/19/style/london-fashion-week-outfits-fashion.html",
    "https://cooking.nytimes.com/recipes/1017937-mississippi-roast",
    "https://astrorobotic.medium.com/seriously-basket-of-deplorables-09f346d78f08",
    "https://astrorobotic.medium.com/please-explain-to-me-for-my-kids-ca6f3ad1e81e",
]


from bs4 import BeautifulSoup
from selenium import webdriver
import urllib.parse
import datetime
import base64
import random

options = webdriver.firefox.options.Options()
options.add_argument("--headless")
with webdriver.Firefox(options=options) as browser:
    for url in pages:
        id = base64.b64encode(url.encode()).decode()  # create an object-unique, reversible id
        if WebPage.exists(index, id): continue        # check whether object exists in filesystem

        browser.get(url)  # download for the html and text fields.
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text = "\n".join([s for p in BeautifulSoup(html, 'html.parser').findAll("p") for s in p.stripped_strings])

        parsed = urllib.parse.urlparse(url)
        domain = ".".join(parsed.hostname.split(".")[-2:])  # construct the domain field; i.e., nytimes.com

        labels = random.choices(["entertainment", "politics", "sports", "news"], k=3)  # generate labels as example
        gps = random.choice([[-42.5188, 172.5718], "38.8974, -77.0365", ["34.034", "-118.6792"]])  # random geo
        ts = random.choice(["Sat Nov 5, 1955 2:15AM", datetime.datetime.now(), "1955-08-01 08:00:00.000"])  # random ts

        WebPage.new(id=id, url=url, domain=domain, html=html, text=text, labels=labels, geo=gps, now=ts).save(index)

# retrieve all from the filesystem; .get(id) .count() .list()
# retrieve all; delete one from filesystem, check count, resave the item.
items = WebPage.getAll(index)
page = items[0]
print(page.url)
WebPage.delete(index, page.id)
print(WebPage.get(index, page.id), WebPage.count(index), WebPage.list(index))
page.save(index)
print(WebPage.count(index), WebPage.list(index))
exit()  # the sections below interact with a dockerized elasticsearch backend using SwiftDataBackend.

########################################################################################################################
# five minute demo: using the database
########################################################################################################################

# SwiftData utilizes the open source ElasticSearch search engine package to create a multi-index search engine server,
# which can exactly model the same SwiftData, and expand to familiar search engine concepts such as analysis and logic.
# The cloudnode package uses docker to containerize all apps and services, and uses passwords as SSL is unnecessary for
# requests made to and from the localhost. For SwiftData, all client management happens entirely in the background, and
# all database management and indexing happens in the background with the same apis as local storage by setting es=True.
# The ElasticSearch data persists across service start/stops; but requires 'snapshots' to be created which equivalent to
# backups of local filestorage. The database also requires refreshing an index after new data is added to query for it.

database_password = "password"
swift = SwiftDataBackend().start(database_password, exist_ok=True, rebuild=True)
WebPage.create_index(index, exist_ok=True)

for item in items:  # if the items are not already in the database; add then the same was as saving to file system
    if not WebPage.exists(index, item.id, es=True):
        item.save(index, es=True)
WebPage.refresh_index(index, es=True)

items_es = WebPage.getAll(index, es=True)  # demonstrate retrieval of all the objects same as pulling file system
assert sorted(WebPage.list(index, es=True)) == sorted(WebPage.list(index, es=False))  # objects are the same, e.g. ids

results = WebPage.search_bar(index, "domain:nytimes.com text:covid")
# results = WebPage.search_bar(index, "labels:politics")
# results = WebPage.search_any(index, "politics")
# results = WebPage.search_any(index, "David")

# snapshots are created as temporal back-ups, i.e., before or after large data migrations; or, to create persistence
# of data after the deletion of its docker container; simply stopping and restarting the docker container will continue
# to persist data, and deletion of the docker container will remove all its contents, except snapshots, which are
# stored in a local filesystem directory, and can be reloaded at any time from any existing snapshot.
swift.snapshot_save(applet)
swift.stop(not_exist_ok=False)
swift.start(database_password, exist_ok=True, rebuild=False)
print(swift.snapshot_list(applet))


# Known issues and improvements. 9/23/24.
# 1. data conversion is not quite right still, and some results are returned as strings
# 2. a bug persists in the docker sdk (owned by docker) for mounting disks
# 3. elasticsearch-dsl requires data get to delete (double pass data)
# 4. field selection is not yet provided (i.e., get returns all fields)
# 5. passwords require breaking down entire container (not communicated to user)
# 6. SQL to elasticsearch-dsl translation not yet enabled.
# 7. FLAGS field not yet implemented; geopoint only searchable withing dsl-q.
# 8. ElasticSearch api calls should be hidden from user unless operating in DEBUG.
# 9. a weird dataclasses quirk requires SwiftData.ts to be string instead of sd.timestamp()