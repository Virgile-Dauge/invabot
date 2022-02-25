import logging
import interactions

from interactions import Embed, Option, Button
#logging.basicConfig(level=logging.DEBUG)

bot = interactions.Client(token=open("bot.token").read()[:-1])

@bot.event
async def on_ready():
    print("Bot is now online.")

@bot.command(name="invasion",
    description="Création du panneau d'inscription",
    scope=906630964703289434,
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="ville",
            description="Dans quelle ville se passe l'invasion ?",
            required=False,
            #choices=[
                #interactions.Choice(name="Choose me! :(", value="choice_one")
                #interactions.Choice(name="Haute-Chute", value="Haute-Chute"),
                #interactions.Choice(name="Grés-du-vent", value="Grés-du-vent")
            #]
        )
    ]

)
async def invasion(ctx: interactions.CommandContext, ville="NomVille"):
    """ Génére un tableau d'inscription dans le channel
    """

    embed = interactions.Embed(
        color= 2003199,
        description="Réagis avec :ballot_box_with_check: à ce message **uniquement si tu es déjà dans le fort**. Attention, retourne vite en jeu, l'auto-AFK kick est rapide (2min). \n\n Si tu as réagi par erreur, merci de décocher ta réaction. :wink:",
        inline=False,
    )
    #embed.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)

    in_bt = interactions.Button(
        style=interactions.ButtonStyle.PRIMARY,
        label="Inscription",
        custom_id="in_callback",
    )
    out_bt = interactions.Button(
        style=interactions.ButtonStyle.SECONDARY,
        label="Désinscription",
        custom_id="out_callback",
    )
    msg = await ctx.send(f"Invasion de {ville}, inscrit-toi **uniquement si tu es dans le fort !**",
                         embeds=embed,
                         components=[in_bt, out_bt])

    #await msg.add_reaction('☑')

    #add_to_hist(ctx.author, msg.id)

    #author_id = dtag(ctx.author)
    #msgs[author_id] = msg.id
    #global msgs_ids
    #msgs_ids += [msg.id]
    #add_to_hist(ctx.author, msg.id)

@bot.component("in_callback")
async def in_callback(ctx: interactions.ComponentContext):
    """ Défini le comportement lorsqu'un joueur s'inscrit
    """
    #print(ctx)
    await ctx.send("Tu es bien inscrit !", ephemeral=True, components=[], embeds=[])

@bot.component("out_callback")
async def out_callback(ctx: interactions.ComponentContext):
    """ Défini le comportement lorsqu'un joueur s'inscrit
    """
    #print(ctx)
    await ctx.send("Tu es bien désinscrit, merci !", ephemeral=True, components=[], embeds=[])

bot.start()
