from cloudnode.base.iaas.nodes.Infrastructure import Infrastructure
import random

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MyAppFunctions:

    @staticmethod
    def george_washington_readers_digest(n_quotes=1):
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
        return random.sample(quotes, n_quotes)


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

# functions are injected by referencing their module.class:function along with other runtime configuration variables
# (such as concurrency and ram limitations); the reason these are referenced by string is so no import requirements
# are made between the function sources and the infrastructure construction and launch. The Infrastructure uses this
# configuration list to load the necessary external modules and construct a REST API; which means these individual
# configuration lines can be passed to any other host machine to also launch which has access to the same repository.
app_functions = [
    dict(source="cloudnode.app:MyAppFunctions.george_washington_readers_digest"),
]

html_functions = [
    dict(source="cloudnode.app:MyHtmlFunctions.front_page"),
]

# Examples for low-level debugging
# curl -X GET http://127.0.0.1:80/functions/MyHtmlFunctions.front_page
# curl -X POST --header "Content-Type: application/json" --data '{"n_quotes": 3}' http://127.0.0.1:5004/functions/MyAppFunctions.george_washington_readers_digest


# Configuration of Service
app_hostport = "0.0.0.0:5004"
html_hostport = "0.0.0.0:80"


class InfrastructureConfig:
    applet = "early"
    username = "davidbernat"

# FIXME: add swift explicitly here.


if __name__ == "__main__":
    Infrastructure.clear().set_admin(InfrastructureConfig.username)  # admin scopes the repository available to server

    # a Servlet is defined as a collection of node functions at a specific hostport (possibly remote) location. For ease
    # of organizing, html functions (i.e., web hosting on port 80) and app functions (port 5004) run on different ports.
    Infrastructure.servlet(app_hostport, app_functions)
    Infrastructure.servlet(html_hostport, html_functions)
    Infrastructure.blocking_start()
