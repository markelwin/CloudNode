from cloudnode import Infrastructure, SwiftData, sd, ServletShiny
import pandas as pd
import dataclasses
import random
import shiny

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

########################################################################################################################
# five-minute demo: hosting dashboards (using Shiny as a search engine)
########################################################################################################################
# Okay. So we cloudnode exists to provide web-first, data-drive, interactive home server applications. How do we begin
# to investigate all our data? What about third-party servlets running concurrently? Can we build dashboard web apps?
# This demo is identical to demo_infrastructure except uses Shiny for Python to build an interactive web application.

# The Shiny for Python system consists of two components: .ui() which is a Shiny UI for rendering inputs and outputs (in
# this case a text box for input query) and an output (the search results); which, when updated, in real-time, execute
# the .server() method to generate its results. (The .output_text_verbatim("results") means that .results() is executed
# for each change of any field in .ui(). The variable input.query() holds the real-time input_text("query", ...) value,
# and, in this case, the direct search into the data frame occurs; no reason to use other backend systems for this.
# Migrate to your browser: http://127.0.0.1:8000/
#
# Or, these still function (which are not related to the search feature):
# curl -X GET http://127.0.0.1:80/functions/MyHtmlFunctions.front_page
# curl -X POST --header "Content-Type: application/json" --data '{"n_quotes": 3}' http://127.0.0.1:5004/functions/MyAppFunctions.george_washington_readers_digest
# curl -X POST http://127.0.0.1:4137/functions/Infrastructure.end


class SearchServlet(ServletShiny):

    @staticmethod
    def ui(request):
        return shiny.ui.page_fluid(
            shiny.ui.input_text("query", "Starlight Crave", placeholder="And?"),
            shiny.ui.output_text_verbatim("results"),
        )

    @staticmethod
    def server(input, output, session):
        @shiny.render.text
        def results():
            print(input)
            q = input.query()
            if q is None or len(q.strip()) == 0: return ""
            query = " " + q.strip().lower()  # only when starts word
            r = df[df['quote'].str.contains(query, case=False)]
            return "\n\n".join(list(r["quote"].values))

@dataclasses.dataclass
class Quotation(SwiftData):
    speaker: sd.string()
    quote: sd.string(analyze=True)
quotes = ["Washington expanded his family estate, Mount Vernon, from 2,000 acres to a whopping 8,000 acres. The property included five separate farms, which grew a variety of crops, including wheat and corn. Managers bred mules, and maintained fruit orchards and a fishery. The vegetable garden itself could feed a family of 14; a necessity, as the President frequently hosted more than 600 guests a year.",
          "In 1797, one of Washington’s estate managers suggested she open a whiskey distillery at Mount Vernon. Washington agreed, and by the time of his death in 1799, the distillery produced nearly 11,000 gallons of whiskey a year, making it the largest producer in America at the time. The distillery still churns out a limited number of bottles each year using its original recipe.",
          "With a 6-foot-2 frame, George Washington was our fourth-tallest President. The tallest was Abraham Lincoln, 6 foot 4, and the shortest was James Madison, at 5 foot 4.",
          "George Washington likely started losing his teeth in his mid-20s at a rate of one tooth each year. He suffered from a lifetime of toothaches, even though his dental hygiene was probably more sophisticated than that of other men at the time. By 1789, the year he was inaugurated, he wore a set of clacking, creaky dentures.",
          "His dentures were not made of wood. Although the wooden-teeth myth prevails, forensic anthropologists found that Washington’s dentures were made from a combination of horse, donkey, and even human teeth. The dentures opened and closed by way of a heavy-duty spring. In order to keep his mouth shut and overpower the spring, Washington would have to keep his mouth clenched. This would have affected the way he looked and spoke.",
          "He created his own dog breed. George Washington loved dogs and fox hunting, so it was only natural for him to want to breed the perfect foxhound. Because of his work, he is occasionally called the father of the American Foxhound. He owned 36 of these pups, and gave them unusually mushy names like Sweet Lips, Tipsy, Venus, and True Love.",
          "Washington met an intelligent and beautiful Sally Fairfax, the woman he is rumored to have loved first, when he was 16. According to researchers at Mount Vernon, she taught him the best manners for moving in Virginia’s highest social circles, and even how to dance the minuet. Sally married one of George’s closest friends, George Williams Fairfax, and the couple visited Mount Vernon frequently. Washington didn’t marry Martha Dandridge Custis until he was 26. Letters show he was still in close contact with Sally at the time.",
          "During the French and Indian War, Washington was lauded as a hero after emerging unscathed from an ambush attack near Fort Duquesne in Pennsylvania. According to several accounts, Washington had two horses shot out from under him, and four bullets pierced his coat.",
          "At the time of George Washington’s death, Mount Vernon had a population of some 318 slaves (123 belonged to him and 153 were dower slaves from Martha Washington’s first husband’s estate), according to anthropologists at Mount Vernon. Before his death, Washington ordered his slaves be freed after Martha’s death. When he died, she freed them, after family members warned her they could easily overthrow her. Sources offer differing insight into Washington’s behavior as a slave owner.",
          "That cherry tree myth? Totally false. The myth was invented by one of Washington’s first biographers, Mason Locke Weems, in The Life and Memorable Actions of Washington. The tall tale first appeared in the book’s fifth edition, published in 1806. Its purpose was to paint Washington as a role model for young Americans, proving that the man’s public greatness was due to his private virtues (honesty, courage, etc.). In 1836, the story was recast as a children’s story, and that’s how rumors spread."]
quotations = [Quotation.new(id=i, speaker="George Washington", quote=q) for i, q in enumerate(quotes)]
df = pd.DataFrame.from_records([q.as_dict() for q in quotations])  # store in a panda dataframe
# in future updates this functionality will be integrated into the same search api as used for complex es=True queries


class MyAppFunctions:

    @staticmethod
    def george_washington_readers_digest(n_quotes=1): return [q.quote for q in random.sample(quotations, n_quotes)]


class MyHtmlFunctions:
    # NOTE: To create an HTML page we specify args=dict(as_type='HTTP') so the NodeFunction processor knows not to json
    # the results (returning its raw string instead) and default to method=["GET"] instead of method=["POST"], etc.
    # NOTE: Notice that within the backend itself the REST APIs are simply functions and can be directly accessed. The
    # purpose here to not only to reduce engineering to single-source implementations but to re-envision hosts and APIs
    # as router-layers which expose already-code functioning occurring within the system processor environment.

    args = dict(as_type="HTTP")

    @staticmethod
    def front_page():
        return \
        """<!DOCTYPE html>
        <html>
        <head>
          <title>Starlight J.A.R.V.I.S.</title>
        </head>
        <body>
        
        <h1> Good morning. </h1>
        <p> 
        JARVIS: Allow me to introduce myself. I am JARVIS, a virtual artificial intellige-- <br/>
        BERNAT: Yeah. Yeah. Yeah. Okay. Let us not get ahead of ourselves here. <br/>
        JARVIS: Here is a fact about George Washington?  <br/>
        BERNAT: That is more our speed under construction. <br/>
        JARVIS: [QUOTE_TO_REPLACE] <br/>
        BERNAT: Thank you, JARVIS. <br/>
        JARVIS: You are welcome, Sir. <br/>
        </p>
        </body>
        </html>""".replace("[QUOTE_TO_REPLACE]", MyAppFunctions.george_washington_readers_digest(n_quotes=1)[0])


app_functions = [
    dict(source="demo_shiny:MyAppFunctions"),
]
html_functions = [
    dict(source="demo_shiny:MyHtmlFunctions"),
]

# Configuration of Service
app_hostport = "0.0.0.0:5004"
html_hostport = "0.0.0.0:80"
shiny_hostport = "0.0.0.0:8000"


class InfrastructureConfig:
    username = "myusername"


if __name__ == "__main__":
    Infrastructure.clear().set_admin(InfrastructureConfig.username)
    Infrastructure.servlet(app_hostport, app_functions)
    Infrastructure.servlet(html_hostport, html_functions)
    Infrastructure.thirdparty(shiny_hostport, SearchServlet)     # integrates thirdparty app
    Infrastructure.blocking_start()
