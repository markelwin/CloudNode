## cloudnode is for building apps on home servers.

cloudnode is built for hosting small single-node servers on home systems in the open-source, and for
engineering containerized apps on top of its core services, including ingress, search, storage, code 
bases, cloud functions, apis, and system logging. These containerized apps can be distributed as any others.

cloudnode is **built for novice engineers** to prevent repeating development across the open-source 
and empower rapid **expand core services** and **prototyping of features**:
- **search** and **storage** using scalable engines
- **self-hosting** of software services and code bases
- **cloud functions** from direct source code
- building from scalable frameworks including **ElasticSearch**

### installation

```
pip install cloudnode
```

[Docker](https://docs.docker.com/engine/install/) is required to host applications including search. 

### Core Components


#### SwiftData
SwiftData is an extension of `dataclasses` built for typed sharing, storage, and search across 
`filesystems` and `ElasticSearch`. It includes ease-of-use tools and can directly spin-up search engines, and interact
with common or complex query types, including `search bar text`, `elasticsearch-dsl`, and `SQL`. SwiftData also extends
fields for working with complex datatypes such as process flags, deep learning embeddings, geospatial data, and others;
see our `SpotifyPlaylist` example and `demo.py` for a full working example of the SwiftData database search system. 

```python
from cloudnode import SwiftData
import dataclasses

@dataclasses.dataclass
class Meme(SwiftData):
    url_image: str
    url_knowyour: str
    text_image: str
```

### five-minute demo: your own search engine

This code sample is part of a full working example in `demo.py`.

```python
from cloudnode import SwiftData, sd, SwiftDataBackend
import dataclasses

@dataclasses.dataclass
class WebPage(SwiftData):
    url: sd.string()                  # an exact string; facilitating exact matches only
    domain: sd.string()
    text: sd.string(analyze=True)     # a body of text; tokenized, analyzed and searchable
    html: sd.string(dont_index=True)  # a string stored in the engine but not intended for search
    labels: sd.string(list=True)      # a list of exact strings; matching one or all is possible
    now: sd.timestamp()               # a timestamp; searchable using windows of time
    geo: sd.geopoint(list=True)       # a list of gps defined spots; searchable via radius

items = []  # see demo.py
applet = "demo"
index = "early"
database_password = "password"

# start the search engine backend
swift = SwiftDataBackend().start(database_password, exist_ok=True, rebuild=True)
WebPage.create_index(index, exist_ok=True)

for item in items:  # if the items are not already in the database; add then the same was as saving to file system
    if not WebPage.exists(index, item.id, es=True):
        item.save(index, es=True)
WebPage.refresh_index(index, es=True)

# familiar search bar queries is one example of how to access search
results = WebPage.search_bar(index, "domain:nytimes.com text:covid")

# snapshots persist after deleting docker
swift.snapshot_save(applet)
print(swift.snapshot_list(applet))
swift.stop(not_exist_ok=False)
```

### Where are the other components? 

We are in the process of porting over from other repositories.

![ferris.bueller.png](cloudnode%2F_db%2Fdocs%2Fferris.bueller.png)

### Licensing & Stuff
<div>
<img align="left" width="100" height="100" style="margin-right: 10px" src="cloudnode/_db/docs/starlight.logo.icon.improved.png">
Hey. I took time to build this. There are a lot of pain points that I solved for you, and a lot of afternoons staring 
outside the coffeeshop window at the sunshine. Not years, because I am a very skilled, competent software engineer. But
enough, okay? Use this package. Ask for improvements. Integrate this into your products. Complain when it breaks. 
Reference the package by company and name. Starlight CloudNode. Email us to let us know!
</div>

#### Hire us to build production.


<br /><br /><br />
Starlight LLC <br />
Copyright 2024 <br />
All Rights Reserved <br />
GNU GENERAL PUBLIC LICENSE <br />
