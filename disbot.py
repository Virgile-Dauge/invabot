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
    intents=disnake.Intents().all(),
    test_guilds=[906630964703289434], # Optional
    sync_commands_debug=True
)

villes = ["Bief de Nérécaille", "Boisclair", "Eaux Fétides", "Gré du vent",
          "Ile des Lames", "Levant", "Haute-Chute", "Marais des Trames",
          "Rive tourmentée", "Val des Larmes", "Falaise du roy"]

async def autocomp_villes(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [ville for ville in villes if user_input.lower() in ville]

async def tags_from_id(ctx, msg_id):
    msg = await ctx.channel.fetch_message(msg_id)
    selected = await msg.reactions[0].users().flatten()
    return [dtag(u) for u in selected][1:]

class CompTrigger(disnake.ui.View):
    def __init__(self, origin, **kwargs):
        super().__init__(**kwargs)
        self.origin = origin
    @disnake.ui.button(label='CB', style=disnake.ButtonStyle.secondary)
    async def cb(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        #msg = await inter.original_message()
        #print(inter.message.id, inter.response.is_done(), msg)
        selected = await tags_from_id(inter, self.origin)
        print(inter.response.is_done())
        #await interaction.edit_original_message(content=f'{len(selected)} Joueurs enregistrés')
        if not inter.response.is_done():
            await inter.response.send_message(content=f'{len(selected)} Joueurs enregistrés')
            print(inter.response.is_done())
        else:
            await inter.edit_original_message(content=f'{len(selected)} Joueurs enregistrés')
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
    trigger = CompTrigger(msg.id, timeout=10*60)
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

@bot.event
async def on_reaction_add(reaction, user):
     if user == bot.user:
         return
     print(user)
     # Récupération des donénes du Gdoc roster
     df = get_roster(config)
     if dtag(user) not in df.index:
         embed = Embed.from_dict(config["embeds"]["dm"])
         embed.description += f'{config["gdoc"]["form"]}) ***!***'
         try:
             await user.send(embed=embed)
         except disnake.errors.HTTPException as e:
             pass
     else:
         guild = reaction.message.guild
         role = guild.get_role(config["ids"]["role"])

         await user.edit(nick=df.at[dtag(user), "Pseudo IG"])
         if role is None:
             # Make sure the role still exists and is valid.
             return

         try:
             # Finally, add the role.
             await user.add_roles(role)
         except disnake.HTTPException:
             # If we want to do something in case of errors we'd do it here.
             pass

bot.run(token=open("bot.token").read()[:-1])
