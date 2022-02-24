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

def main():
    bot = commands.Bot(
        intents=disnake.Intents().all(),
        test_guilds=[906630964703289434], # Optional
        sync_commands_debug=True
    )
    # Chargement de la config du bot
    def load_data(path='data.json'):
        with open(path, 'r') as datafile:
            return json.load(datafile)
    def save_data(data, path='data.json'):
        with open(path, 'w') as datafile:
            json.dump(data, datafile, sort_keys=True, indent=4)
    def add_participation(participants):
        #print(participants)
        data = load_data()
        for p in participants:
            if p in data:
                data[p] +=1
            else:
                data[p] = 1
        #print(data)
        save_data(data)
    
    async def autocomp_sources(ctx: disnake.ApplicationCommandInteraction, user_input: str):
        voices = [v for v in ctx.guild.voice_channels if v.members]
        return [v.name for v in voices if v.name.lower().startswith(user_input.lower())]
    
    async def autocomp_destinations(ctx: disnake.ApplicationCommandInteraction, user_input: str):
        voices = ctx.guild.voice_channels
        return [v.name for v in voices if v.name.lower().startswith(user_input.lower())]
        #return [ville for ville in villes if user_input.lower() in ville]
    @bot.slash_command()
    async def transfert(ctx: disnake.ApplicationCommandInteraction,
                        source: str=commands.Param(autocomplete=autocomp_sources),
                        destination: str=commands.Param(autocomplete=autocomp_destinations)):
        """Déplace les joueurs d'un salon vocal source à un salon destinatoin
    
            Parameters
            ----------
            source: La ville où se déroule l'invasion
            destination: La ville où se déroule l'invasion
        """
        voices = {v.name: v for v in ctx.guild.voice_channels}
        dest = voices[destination]
        users = voices[source].members
        await ctx.send(content=f'{len(users)} Utilisateurs vont être déplacés dans le salon ***{destination}***', ephemeral=True)
        [await u.move_to(dest) for u in users]
    
    
    villes = ["Bief de Nérécaille", "Boisclair", "Eaux Fétides", "Gré du vent",
              "Ile des Lames", "Levant", "Haute-Chute", "Marais des Trames",
              "Rive tourmentée", "Val des Larmes", "Falaise du roy"]
    
    async def autocomp_villes(inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [ville for ville in villes if ville.lower().startswith(user_input.lower())]
    
    async def tags_from_id(ctx, msg_id):
        msg = await ctx.channel.fetch_message(msg_id)
        selected = await msg.reactions[0].users().flatten()
        return [dtag(u) for u in selected][1:]
    
    class CompTrigger(disnake.ui.View):
        options = [disnake.SelectOption(label=k, value=v) for k, v in config['gdoc']['strats'].items()]
        options[0].default = True
        def __init__(self, origin, **kwargs):
            super().__init__(**kwargs)
            self.origin = origin
            self.strat = config['gdoc']['strats']['Principale']
    
        @disnake.ui.select(options=options)
        async def compo(self, select: disnake.ui.Select, inter: disnake.MessageInteraction):
            self.strat=select.values[0]
            await inter.response.defer()
    
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
        async def trigger(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
            #await interaction.delete_original_message()
            await inter.response.defer()
            self.stop()
    
    
    @bot.slash_command(
        scope=906630964703289434,
    )
    async def invasion(
            ctx: disnake.ApplicationCommandInteraction,
            ville: str=commands.Param(autocomplete=autocomp_villes)):
        """ Génére un tableau d'inscription dans le channel actuel
    
            Parameters
            ----------
            ville: La ville où se déroule l'invasion
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
    
        add_participation(roster.index)
    
        strat=trigger.strat
    
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
    
    @bot.slash_command(
        description="Vérification du Gdoc et mise à jour des rôles",
        scope=906630964703289434,
    )
    async def verif(ctx):
        """ Attribue les rôles
        """
    
        guild = ctx.guild
        lead_role = guild.get_role(config["ids"]["leads"])
    
        # Récupération des donénes du Gdoc roster
        roster_df = get_roster(config)
        roster = list(roster_df.index)
    
        members = {dtag(m): m for m in guild.members}
    
        role = guild.get_role(config["ids"]["role"])
        verified = [dtag(m) for m in role.members]
    
        added = []
        wrong = []
        for u in roster:
           if u not in members:
               wrong += [u]
           elif u not in verified:
               if role is None:
                   # Make sure the role still exists and is valid.
                   return
    
               try:
                   # Finally, add the role.
                   await members[u].add_roles(role)
                   added += [u]
               except discord.HTTPException:
                   # If we want to do something in case of errors we'd do it here.
                   pass
    
        removed = []
        for u in verified:
            if u not in roster:
                try:
                    # Finally, remove the role.
                    await members[u].remove_roles(role)
                    removed += [u]
    
                    # Send DM to user
                    embed = Embed.from_dict(config["embeds"]["change"])
                    embed.description += f'{config["gdoc"]["form"]}) ***!***'
                    await members[u].send(embed=embed)
                except discord.HTTPException:
                    # If we want to do something in case of errors we'd do it here.
                    pass
    
        def list_to_field(l):
            f = 'aucun'
            if l:
                f = ''
                for u in l:
                    f += u + '\n'
            if len(f)>1023:
                return f[:1000]+'...'
            return f
    
        def add_IG(l, roster_df):
            return [f"{i} | {roster_df.loc[i]['Pseudo IG']}" for i in l]
        wrong = add_IG(wrong, roster_df)
        added = add_IG(added, roster_df)
        embed = Embed()
        embed.title = f'Vérification du gdoc'
        embed.color = 2003199
        #embed.set_footer(text=ctx.author.name, icon_url = ctx.author.avatar_url)
    
        embed.add_field(name="Joueurs nouvellement vérifiés", value=list_to_field(added), inline=False)
        embed.add_field(name="Discord tag dans le Gdoc ne correspondant à aucun membre du discord", value=list_to_field(wrong), inline=False)
        embed.add_field(name=f"Joueurs ayant changé de Discord tag (rôle {role} supprimé)", value=list_to_field(removed), inline=False)
        await ctx.channel.send(embed=embed, delete_after=20*60)
        #print(added, wrong)
    
    
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

if __name__ == "__main__":
    main()
