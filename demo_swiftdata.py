from cloudnode import SwiftData, SwiftDataBackend, sd, RuntimeConfig
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This demo creates a simple book search engine.
silo = "demo"    # a silo of indices in the search repository; i.e., Book index=demo and index=prod are different dbs

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
# Users interact with these filesystem version exactly the same as the search api calls by setting the db=False flag in
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

class Book(SwiftData):
    title: sd.string(analyze=True)     # a string of text; tokenized, and analyzed for varied searchable
    authors: sd.string(list=True)      # a list of exact strings; facilitating exact matches only
    isbn: sd.string()                  # an exact string; facilitating exact matches only
    year: sd.integer()                 # an integer; searchable by range and equality
    subtitle: sd.string(analyze=True)  # a string of text; tokenized, and analyzed for varied searchable
    # now: sd.timestamp()               # a timestamp; searchable using windows of time
    # geo: sd.geopoint(list=True)       # a list of gps defined spots; searchable via radius

data = [
["Courtiers",	        "Valentine Low",    "978-1-250-28256-9",        "2022",     "Intrigue, Ambition, And The Power Players Behind The House Of Windsor"],
["Genius Makers",	    "Cade Metz",        "978-1-524-74267-6",        "2021",     "The Mavericks Who Brought AI To Google, Facebook, And The World"],
["Equilibrium Statistical Physics",	"Michael Plischke & Birger Bergersen", "981-0-21642-4", "1994", ""],
["The Four",	        "Scott Galloway",   "978-0-735-213678",         "2018",     "The Hidden DNA Of Amazon, Apple, Facebook, And Google"],
["On Call",	            "Anthony Fauci",    "978-0-593-65747-8",        "2024",     "A Doctor's Journey In Public Service"],
["Memoir!",	            "Sid Meier",        "978-1-324-00587-2",        "2020",     "A Life In Computer Games"],
["Reality Is Broken",	"Jane McGonigal",   "978-0-143-12061-2",        "2011",     "Why Games Make Us Better And How They Can Change The World"],
["What to Eat When You're Pregnant",    "Nicole Avena", "978-1-607-74679-9", "2015", "A Week-By-Week Guide To Support Your Health And Your Baby's Development"],
["Chaos Monkeys",	    "Antonio Garcia Martinez",  "978-1-785-03646-0","2017",     "Mayhem And Mania Inside The Silicon Valley Money Machine"],
["Flight of the WASP",	"Michael Gross",    "978-0-8021-6186-4",        "2023",     "The Rise, Fall, And Future Of America's Original Ruling Class"]]

for (title, authors, isbn, year, subtitle) in data:
    # we will use the isbn as the id field; and split authors into a list.
    id = isbn
    authors = authors.split(" & ") if "&" in authors else [authors]
    if Book.exists(silo, id): continue  # check whether object exists in filesystem
    Book.new(id=id, title=title, authors=authors, isbn=isbn, year=year, subtitle=subtitle).save(silo)  # save to disk

# retrieve all from the filesystem; .get(id) .count() .list()
# retrieve all; delete one from filesystem, check count, resave the item; check again
books = Book.getAll(silo)
book = books[0]
print(book.isbn)
Book.delete(silo, book.id)
print(Book.get(silo, book.id), Book.count(silo), Book.list(silo))
book.save(silo)
print(Book.count(silo), Book.list(silo))
# exit()  # the sections below interact with a meilisearch running as backend for SwiftDataBackend.

########################################################################################################################
# five minute demo: using the database
########################################################################################################################

# SwiftData utilizes on-premise self-hosting Meilisearch search engine to create a multi-application search server for
# your cloudnode applications, using the exact same SwiftData data models whether you save-to-disk or use Meilisearch.
# To install Meilisearch follow the directions on its installation page and set a passkey at MEILISEARCH_SERVER_PASSKEY.
# SwiftData creates a global backend client which is accessed automatically whenever SwiftData objects are with db=True.
# If a Meilisearch server is already running somewhere else all that needs to be done is point SwiftDataBackend to it.
# Note: For the time being we are disabling the server_start from within cloudnode; start the server externally instead.
database_passkey = os.environ['MEILISEARCH_SERVER_PASSKEY']
database_hostport = "http://meilisearch.jarvis.home"  # its default unless set
swift = SwiftDataBackend(database_hostport, database_passkey)
# swift = SwiftDataBackend(database_hostport, database_passkey).start_server(exist_ok=True)  # disabled temporarily

Book.delete_index(silo)
Book.create_index(silo, exist_ok=True)
print([Book.exists(silo, book.id, db=True) for book in books])
# for book in books:  # if the items are not already in the database; add then the same was as saving to file system
#     if not Book.exists(silo, book.id, db=True): book.save(silo, db=True)
Book.saveAll(silo, [book for book in books if not Book.exists(silo, book.id, db=True)], db=True)  # or, in parallel

db_items = Book.getAll(silo, db=True)  # demonstrate retrieval of all the objects same as pulling file system
assert sorted(Book.list(silo, db=True)) == sorted(Book.list(silo, db=False))  # objects are the same, e.g. ids

results = Book.search_bar(silo, 'Games')
results = Book.search_bar(silo, 'subtitle: Games')
results = Book.search_bar(silo, 'subtitle: Games authors: "Jane McGonigal"')
results = Book.search_bar(silo, 'subtitle: Games autohrs: "Jane McGonigal"')  # misspelled excluded; creates warning
results = Book.search_bar(silo, "~subtitle: Facebook Google")


# Known issues and improvements. 3/1/25.
# 1. FLAGS field not yet implemented; geopoint, vector search support incomplete.
# 2. documentation, and others.
# 3. search via filesystem not implemented yet
# 4. search via search_bar only handles string fields; no direct access to db_client yet provided purposefully