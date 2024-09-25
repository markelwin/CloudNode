from cloudnode import GenericCloudClient, ReturnType, AetherClient

# r = GenericCloudClient.request("http://127.0.0.1:5004/functions/MyAppFunctions.george_washington_readers_digest",
#                                d=dict(n_quotes=3), method="POST", rtype=ReturnType.JSON)

# r = AetherClient.request("ae://MyAppFunctions.george_washington_readers_digest", d=dict(n_quotes=3))
r = AetherClient.request("ae://Infrastructure.end")
print()