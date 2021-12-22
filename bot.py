import pandas as pd
from algo import build_comp

import discord
from discord.ext import commands

# Chargement de la config du bot
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)

# Chargement du token
with open('bot.token', 'r') as datafile:
    token = datafile.read()

def dtag(user):
    return f'{user.name}#{user.discriminator}'

import pandas as pd
def get_roster(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_roster']}"
    #return pd.read_csv(url).iloc[1:, 0:6].dropna().set_index('dtag')
    return pd.read_csv(url).set_index('dtag')

def get_strat(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_strat']}"
    return pd.read_csv(url).iloc[0:5, 0:12]

bot = commands.Bot(command_prefix="!")

msgs = {}
msgs_ids = []

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    game = discord.Game("Venez chez Bakhu")
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.command()
async def inva(ctx, arg):
    """ Génére un tableau d'inscription dans le channel
    """
    embed = discord.Embed.from_dict(config["embeds"]["panneau"])
    embed.title += f' {arg}'
    embed.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)

    msg = await ctx.channel.send(embed=embed)
    await msg.add_reaction('☑')

    author_id = dtag(ctx.author)
    msgs[author_id] = msg.id
    global msgs_ids
    msgs_ids += [msg.id]

@bot.command()
async def comp(ctx):
    """ Génére une composition d'armée
    """
    author_dtag = dtag(ctx.author)
    channel = ctx.channel

    # On s'assure que l'utilisateur qui demande le calcul ait déjà fait la commande principale
    if author_dtag not in msgs:
        await channel.send(f"Pas de messages trouvés pour {author_dtag}. Commencez par utiliser la commande :\n $inva nomVille")
        return

    # Récupération du message avec les réacs
    msg_id = msgs[author_dtag]
    main_msg = await channel.fetch_message(msg_id)

    # Récupération de la liste des users
    selected = await main_msg.reactions[0].users().flatten()
    selected_tags = [dtag(u) for u in selected][1:]
    selected_snow = {t: u.id for t, u in zip(selected_tags, selected)}

    # Récupération des donénes du Gdoc roster
    roster = get_roster(config)

    # Joueurs séléctionnés n'ayant pas rempli le Gdoc
    not_registered = [u for u in selected_tags if u not in roster.index]

    # Filtrage du roster avec les joueurs séléctionnés
    roster = roster.filter(items=selected_tags, axis=0).set_index('Pseudo IG')
    print(roster)
    # Récupération de la strat
    strat = get_strat(config)
    comp = build_comp(roster, strat)
    await channel.send(comp)

@bot.event
async def on_reaction_add(reaction, user):
     # On vérifie que la réaction est sur un message panneau
     if reaction.message.id not in msgs_ids:
         return
     if user == bot.user:
         return

     # Récupération des donénes du Gdoc roster
     df = get_roster(config)
     if dtag(user) not in df.index:
         embed = discord.Embed.from_dict(config["embeds"]["dm"])
         embed.description += f'{config["gdoc"]["url"]}) ***!***'
         try:
             await user.send(embed=embed)
         except discord.errors.HTTPException as e:
             pass
     else:
         # Plus tard, ajouter l'utilisateur aux tryhard s'il n'y est pas déjà
         pass

bot.run(token)
