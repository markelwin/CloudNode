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

## Core Components

### SwiftData
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

### EasyAPI & Infrastructure

`EasyAPI` exists to transfer functions from locked-on-the-computer resources to exposed, secure world-wide-web APIs, and
`Infrastructure` exists to transform any system of code to a backend SDK for constructing applications. With these two
resources the difference between code you construct for processing the computer and exposed across applications shrinks
to zero. 




### five-minute demo: your own search engine

This code sample is part of a full working example in `demo_swiftdata.py`.

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

items = []  # see demo_swiftdata.py
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

### five-minute demo: EasyAPI

It may not look like much yet but the fundamentals here are very important. With just the same effort as building a 
Python function, the software can be injected into modern API frameworks complete with authentication, cloud logging,
performance statistics, and transformed into modern cloud functions hosted on a home server or any external computer.

Infrastructure code and configurations are kept entirely separated from software code so that every function can be
built into infrastructure without requiring entangling of imports, and maintaining clean code.

This code sample is part of a full working example in `demo_easyapi.py` to show the fundamentals of building functions
which become backend data services or dynamic webpages and more. This package is an early release and still contains 
numerous imperfections and mistakes, and edge cases which will be handled from our existing solutions in new releases.

![demo_easyapi.png](cloudnode%2F_db%2Fdocs%2Fdemo_easyapi.png)

```python
from cloudnode import Infrastructure

class MyAppFunctions:
    
    @staticmethod
    def george_washington_readers_digest(n_quotes=1): pass

app_functions = [
    dict(source="demo_easyapi:MyAppFunctions.george_washington_readers_digest"),
]

app_hostport = "0.0.0.0:5004"
username = "myusername"
    
Infrastructure.clear().set_admin(username)
Infrastructure.servlet(app_hostport, app_functions)
Infrastructure.blocking_start()
```

### five-minute demo: Infrastructure

We have `SwiftData` for storage and search and `Infrastructure` for hosting data and web servers?

This code sample is part of a full working example in `demo_infrastructure.py`.

![demo_infrastructure.png](cloudnode%2F_db%2Fdocs%2Fdemo_infrastructure.png)

### five-minute demo: interative data-driven api web applications

Okay. We have `SwiftData` data-intense backends. What about front-ends?

This code sample is part of a full working example in `demo_shiny.py`.

![demo_shiny.png](cloudnode%2F_db%2Fdocs%2Fdemo_shiny.png)


### Where are the other components? 

We are in the process of porting over from other repositories.

![ferris.bueller.png](cloudnode%2F_db%2Fdocs%2Fferris.bueller.png)

### What kinds of hardware are we talking about?

Inexpensive. The 3.4GHz 8GB Ace Magician is more than enough to run home servers with compute equivalent to nearly
modern laptops. The external 2TB hard drive is useful for data storage when working with video or heavy data compute,
and the monitor helps with debugging and seconds as a television screen. The motherboard of Ace Magician is not 
sufficient for hosting external GPUs, such as for deep learning, but a shocking amount of two-year old deep learning can
be run effortlessly on CPUs, and we will cover GPUs when we begin hosting distributed GPU deep learning compute 
infrastructures ourselves at Starlight. This setup easily lasts for more than two or three years which means that $200 
can put a home server in any home, garage, workshop, school, or curious student bedroom.

- [ ] [Ace Magician Mini PC 8GB RAM 256GB SSD 3.4GHz ($160)](https://www.walmart.com/ip/Mini-PC-Intel-N95-8GB-RAM-256GB-SSD-3-4GHz-Desktop-Computer-Windows-11-Pro/573864485) 
- [ ] [Seenda Bluetooth Wireless Keyboard ($15)](https://www.walmart.com/ip/seenda-Bluetooth-Wireless-Keyboard-Windows-Mac-Rechargeable-Slim-Multi-Device-2-4G-USB-Dual-BT4-0-Computer-Laptop-Android-MacBook-Pro-Air-Chromebook/988516094)
- [ ] [Logitech Wireless Mouse ($10)](https://www.walmart.com/ip/Logitech-Silent-Wireless-Mouse-2-4-GHz-with-USB-Receiver-1000-DPI-Optical-Tracking-Black/484306986)

Optional:
- [ ] [Acer 17" Widescreen LCD Monitor ($38)](https://www.walmart.com/ip/Acer-17-Widescreen-LCD-Monitor-Display-SXGA-1280-X-1024-5-ms-TN-Film/27943318)
- [ ] [HDMI (male) to VGA (female) Adapter ($5)](https://www.walmart.com/ip/CableVantage-HDMI-Male-to-VGA-Female-Video-Converter-Adapter-Cable-For-PC-DVD-1080P-HDTV-TV/781975578?classType=REGULAR&from=/search)
- [ ] [GE 6-Outlet 2-ft Surge Protector ($9)](https://www.walmart.com/ip/GE-Pro-15-Amp-Grounded-6-Outlet-Surge-Protector-with-2-ft-Braided-Extension-Cord-Black/355272429)
- [ ] [SanDisk 2TB Portable External SSD ($69)](https://www.walmart.com/ip/SanDisk-2TB-Portable-External-SSD-up-to-680MB-s-USB-C-USB-3-2-Gen-2-SDSSDE29-2T00-AW25/1687049704)


### Licensing & Stuff
<div>
<img align="left" width="100" height="100" style="margin-right: 10px" src="cloudnode/_db/docs/starlight.logo.icon.improved.png">
Hey. I took time to build this. There are a lot of pain points that I solved for you, and a lot of afternoons staring 
outside the coffeeshop window at the sunshine. Not years, because I am a very skilled, competent software engineer. But
enough, okay? Use this package. Ask for improvements. Integrate this into your products. Complain when it breaks. 
Reference the package by company and name. Starlight CloudNode. Email us to let us know! We will be transitioning to a 
managed open-source license at some point to protect our internal intellectual property.
</div>

#### Hire us to build production.


<br /><br /><br />
Starlight LLC <br />
Copyright 2024 <br />
All Rights Reserved <br />
GNU GENERAL PUBLIC LICENSE <br />
