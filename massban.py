import requests

GUILD_ID = 999198124394430464
TOKEN = 'MTIzMTc0ODU4MDIwMTczMDA3OQ.Gz7wHV.SI69fbyk0sUfiShkFF5XOUXdmrJTtCoiUiJEH4' # bot token
REASON = 'spy.pet bot - adios!'

selfbots = requests.get('https://gist.githubusercontent.com/Dziurwa14/05db50c66e4dcc67d129838e1b9d739a/raw/b0c0ebba557521e9234074a22e544ab48f448f6a/spy.pet%20accounts').json()
requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/bulk-ban", headers={
  'Authorization': 'Bot ' + TOKEN, 'X-Audit-Log-Reason': REASON
}, json={'user_ids': selfbots})