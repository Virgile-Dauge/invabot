# Chargement de la config du bot
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)

with open('bot.token', 'r') as datafile:
    token = datafile.read()

def dtag(user):
    return f'{user.name}#{user.discriminator}'

def get_roster(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_roster']}"
    print(pd.read_csv(url).iloc[1:, 0:6].dropna().set_index('dtag'))
    return pd.read_csv(url).iloc[1:, 0:6].dropna().set_index('dtag')

def get_strat(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_strat']}"
    return pd.read_csv(url).iloc[0:5, 0:12]

import pandas as pd
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="$")

msgs = {}
msgs_ids = []

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    game = discord.Game("Venez chez Bakhu")
    await bot.change_presence(status=discord.Status.online, activity=game)

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


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$inva'):

        embed = discord.Embed.from_dict(config["embeds"]["panneau"])
        embed.title += f'{message.content[5:]}'

        msg = await message.channel.send(embed=embed)
        await msg.add_reaction('☑')

        author_id = dtag(message.author)
        msgs[author_id] = msg.id
        global msgs_ids
        msgs_ids += [msg.id]

    if message.content.startswith('$invc'):

        author_dtag = dtag(message.author)
        channel = message.channel

        # On s'assure que l'utilisateur qui demande le calcul ait déjà fait la commande principale
        if author_dtag not in msgs:
            await channel.send(f"Pas de messages trouvés pour {author_dtag}. Commencez par utiliser la commande :\n $inva nomVille")
            return

        # Récupération du message avec les réacs
        msg_id = msgs[author_dtag]
        main_msg = await message.channel.fetch_message(msg_id)

        # Récupération de la liste des users
        selected = await main_msg.reactions[0].users().flatten()
        selected_tags = [dtag(u) for u in selected][1:]
        selected_snow = {t: u.id for t, u in zip(selected_tags, selected)}
        await channel.send(f'Joueurs séléctionés : {selected}')

        # Récupération des donénes du Gdoc roster
        df = get_roster(config)

        # Joueurs séléctionnés n'ayant pas rempli le Gdoc
        not_registered = [u for u in selected_tags if u not in df.index]

        # Filtrage du gdoc avec les joueurs séléctionnés
        df = df.filter(items=selected, axis=0)
        print(selected, not_registered, df)

bot.run(token)
