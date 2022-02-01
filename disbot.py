import pandas as pd
from algo import build_comp

import disnake
from disnake.ext import commands
from disnake import Embed, Emoji


def dtag(user):
    return f'{user.name}#{user.discriminator}'
def get_roster(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_roster']}"
    #return pd.read_csv(url).iloc[1:, 0:6].dropna().set_index('dtag')
    return pd.read_csv(url).set_index('dtag')
# Chargement de la config du bot
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)

bot = commands.Bot(
    command_prefix='!',
    test_guilds=[906630964703289434], # Optional
    sync_commands_debug=True
)

@bot.slash_command()
async def ping(inter):
    await inter.response.send_message("Pong!")

villes = ["Bief de Nérécaille", "Boisclair", "Eaux Fétides", "Gré du vent",
          "Ile des Lames", "Levant", "Haute-Chute", "Marais des Trames",
          "Rive tourmentée", "Val des Larmes", "Falaise du roy"]

async def autocomp_villes(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [ville for ville in villes if user_input.lower() in ville]

class CompTrigger(disnake.ui.View):
    @disnake.ui.button(label='Composition', style=disnake.ButtonStyle.blurple)
    async def trigger(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        #await interaction.delete_original_message()
        self.stop()

@bot.slash_command(
    description="Création du panneau d'inscription",
    scope=906630964703289434,
)
async def invasion(
        ctx: disnake.ApplicationCommandInteraction,
        ville: str=commands.Param(autocomplete=autocomp_villes)):
    """ Génére un tableau d'inscription dans le channel
    """

    embed = Embed(
        title=f'Invasion de {ville}',
        color=2003199,
        description="Réagis avec :ballot_box_with_check: à ce message **uniquement si tu es déjà dans le fort**. Attention, retourne vite en jeu, l'auto-AFK kick est rapide (2min). \n\n Si tu as réagi par erreur, merci de décocher ta réaction. :wink:",
    )
    #embed.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)

    # Envoi du message et ajout de la réaction
    await ctx.send(embed=embed)
    msg = await ctx.original_message()
    await msg.add_reaction('☑')

    # Envoi d'un message caché à l'invocateur
    trigger = CompTrigger()
    await ctx.send("Calcul", view=trigger, ephemeral=True)

    # Attente du déclanchement pas l'invocateur
    await trigger.wait()

    # Récupération du message originel complet
    msg = await ctx.channel.fetch_message(msg.id)

    selected = await msg.reactions[0].users().flatten()

    selected_tags = [dtag(u) for u in selected][1:]

    # Récupération des donénes du Gdoc roster
    roster = get_roster(config)

    # Joueurs séléctionnés n'ayant pas rempli le Gdoc
    not_registered = [u for u in selected_tags if u not in roster.index]

    # Filtrage du roster avec les joueurs séléctionnés
    roster = roster.filter(items=selected_tags, axis=0).set_index('Pseudo IG')
    print(roster)

    strat='Strat_principale'
    # Récupération de la strat
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={strat}"

    page = pd.read_csv(url)
    strat_df = page.iloc[0:5, 0:10]
    img_url = page.iat[5, 1]

    comp = build_comp(roster, strat_df, config)
    def gen_embed(comp):
       e = Embed(title="Composition d'armée")
       for k, v in comp.iteritems():
           f = ''
           for p in v.to_list():
               f += str(p) + '\n'
           e.add_field(name=k, value=f, inline=True)
       return e
    
    
    embed = gen_embed(comp)
    embed.title = f"Invasion de {ville}, {strat} :"
    #embed.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)
    embed.color = 2003199
    embed.set_thumbnail(url=img_url)
    await ctx.send(embed=embed, delete_after=60*25)
bot.run(token=open("bot.token").read()[:-1])
