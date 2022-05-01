# This file is part of Invabot.

# Invabot is free software: you can redistribute it
# and/or modify it under the terms of the GNU General 
# Public License as published by the Free Software
# Foundation, either version 3 of the License, or 
# any later version.

# Invabot is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License
# for more details.

# You should have received a copy of the GNU General
# Public License along with Invabot. If not, see
# <https://www.gnu.org/licenses/>

import pandas as pd
from algo import build_comp

# Chargement de la config du bot
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)

# Chargement de la config du bot
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)

# Chargement du token
with open('bot.token', 'r') as datafile:
    token = datafile.read()

def dtag(user):
    return f'{user.name}#{user.discriminator}'

def get_roster(config):
    url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_roster']}"
    #return pd.read_csv(url).iloc[1:, 0:6].dropna().set_index('dtag')
    return pd.read_csv(url).set_index('dtag')

def get_strat(config, strat=None):
    if strat is None:
        url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_strat']}"
    else:
        url = f"{config['gdoc']['url']}gviz/tq?tqx=out:csv&sheet={config['gdoc']['page_strat']}"
    return pd.read_csv(url).iloc[0:5, 0:12]

import pandas as pd
from algo import build_comp

import disnake
from disnake.ext import commands
from disnake import Embed, Emoji

import re


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
def list_to_field(l):
    f = 'aucun'
    if l:
        f = ''
        for u in l:
            f += u + '\n'
        if len(f)>1023:
            return f[:1000]+'...'
        return f

def unique(l):
    u = []
    for r in l:
        if r not in u:
            u +=[r]
    return u

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
        embed.set_footer(text='Invasion')
    
        # Envoi du message et ajout de la réaction
        await ctx.send(embed=embed)
        msg = await ctx.original_message()
        await msg.add_reaction('☑')
    
        # Création du vocal
        invasions_cat = 906648457824051252
        category = disnake.utils.find(lambda c: c.id == invasions_cat, ctx.guild.categories)
    
        await category.create_voice_channel(f'🔩 Réparations {ville}')
        await category.create_voice_channel(f'{ville}', user_limit=99)
    
        # Envoi d'un message caché à l'invocateur
        trigger = CompTrigger(msg.id, timeout=10*60)
        await ctx.send("Calcul", view=trigger, ephemeral=True)
    
        # Attente du déclanchement pas l'invocateur
        await trigger.wait()
    
        # Récupération du message originel complet
        msg = await ctx.channel.fetch_message(msg.id)
    
        selected = await msg.reactions[0].users().flatten()
    
        selected_tags = [dtag(u) for u in selected if dtag(u) != 'Invasion#5489']
        #selected_tags = [dtag(u) for u in selected][1:]
    
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
    
    donjons = ["Lazarus", "Gènese", "Dynastie", "Etoile", "Profondeur", "Amrine"]
    zones_elites = ["Sirène", "Palais", "Mines", "Myrk", "Malveillance"]
    lieux = donjons + zones_elites
    async def autocomp_lieux(inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [l for l in lieux if l.lower().startswith(user_input.lower())]
    
    @bot.slash_command()
    async def instance(ctx: disnake.ApplicationCommandInteraction,
                       lieu: str=commands.Param(autocomplete=autocomp_lieux),
                       heure: str=commands.Param(default=None),
                       prix: str=commands.Param(default=None),
                       tanks: int=commands.Param(default=None),
                       dps: int=commands.Param(default=None),
                       heals: int=commands.Param(default=None),
                       mutation: int=commands.Param(default=None)):
        """Crée un panneau d'inscription à une instance
    
            Parameters
            ----------
            lieu: La ville où se déroule l'instance
            heure: L'heure à laquelle se déroule l'instance
            prix: Le prix par personne, gratuit c'est cool aussi ;)
            tanks: Le nombre de tanks attendus
            dps: Le nombre de dps attendus
            heals: Le nombre de heals attendus
            mutation: Le niveau de mutation (si mutation)
        """
        embed = Embed()
        embed.title = f'Instance {lieu}'
        if mutation:
            embed.title += f' M{mutation}'
        embed.description = ''
        if heure:
            embed.description += f' 🕐 {heure}\n'
        if prix:
            embed.description += f' 💰 {prix}\n'
        embed.description += f'Proposée par {ctx.user.mention}\n'
        embed.color = 2003199
    
        # Si nombre custom
        if tanks or dps or heals:
            if not tanks:
                tanks = 1
            if not dps:
                dps = 3
            if not heals:
                heals = 1
            roles = ['🛡']*tanks + ['⚔']*dps + ['⛑']*heals
        else:
            roles = ['🛡', '⚔', '⚔', '⚔','⛑']
    
        players = ['libre']*len(roles)
        embed.add_field(name="Rôles", value=list_to_field(roles), inline=True)
        embed.add_field(name="Joueurs", value=list_to_field(players), inline=True)
        embed.set_footer(text='Instance')
        # Envoi du message et ajout de la réaction
        await ctx.send(embed=embed)
        msg = await ctx.original_message()
    
    
        for r in unique(roles):
            await msg.add_reaction(r)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
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
               except disnake.HTTPException:
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
                except disnake.HTTPException:
                    # If we want to do something in case of errors we'd do it here.
                    pass
    
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
    
    
    import math
    def progress_bar(percent, full='🟩', empty='⬜'):
        done = math.floor(percent*10)
        return full* done + empty*(10-done) + ' ' + f'{percent*100:.1f}%'
    
    def display_progress(actuel, objectif):
        def display_num(n):
            s = str(n)
            if s.endswith('000'):
                s = s[:-3] + 'k'
            return s
        return display_num(actuel)+ ' ̸ ' + display_num(objectif) + ' ' + progress_bar(actuel/objectif, full='▆', empty='▁')
    
    def progress_embed(title, actuel, objectif, contrib={}, top=5):
        embed = disnake.Embed()
        embed.title = title
        embed.description = display_progress(actuel, objectif)
    
        contrib_str=''
        if contrib:
            s = dict(sorted(contrib.items(), key=lambda item: item[1], reverse=True))
            for k, v in s.items():
                contrib_str += f'{k}  {v}\n'
            embed.add_field('Contributeurs', contrib_str)
        return embed
    
    class Dropdown(disnake.ui.Select):
      def __init__(self, **kwargs):
    
          # Set the options that will be presented inside the dropdown
          options = [
              disnake.SelectOption(
                  label="1",
              ),
              disnake.SelectOption(
                  label="10",
              ),
              disnake.SelectOption(
                  label="100",
              ),
              disnake.SelectOption(
                  label="1000",
              ),
          ]
    
          # The placeholder is what will be shown when no option is chosen
          # The min and max values indicate we can only pick one of the three options
          # The options parameter defines the dropdown options. We defined this above
          super().__init__(
              placeholder="Valeur",
              min_values=1,
              max_values=1,
              options=options,
              **kwargs
          )
    
      async def callback(self, interaction: disnake.MessageInteraction):
          await interaction.response.defer()
    
    class ProgressView(disnake.ui.View):
        def __init__(self, title, objectif):
            super().__init__(timeout=None)
            self.title = title
            self.actual = 0
            self.objectif = objectif
            self.contributors = {}
            #self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.secondary,
            #                                label=display_progress(0, objectif),
            #                                row=0, disabled=True))
            #self.add_item(Dropdown(row=0))
    
        async def update(self, val, interaction: disnake.MessageInteraction):
            #self.actual = self.actual + int(self.children[-1].values[0])
            self.actual = self.actual + val
            author = interaction.author.mention
            if author not in self.contributors:
                self.contributors[author] = val
            else:
                self.contributors[author] += val
            await interaction.response.edit_message(embed=progress_embed(self.title,
                                                                         self.actual,
                                                                         self.objectif,
                                                                         self.contributors))
    
        @disnake.ui.button(label="+1", style=disnake.ButtonStyle.green, row=0)
        async def ajout1(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await self.update(1, interaction)
    
        @disnake.ui.button(label="+10", style=disnake.ButtonStyle.green, row=0)
        async def ajout10(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await self.update(10, interaction)
    
        @disnake.ui.button(label="+100", style=disnake.ButtonStyle.green, row=0)
        async def ajout100(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await self.update(100, interaction)
    
        @disnake.ui.button(label="+1000", style=disnake.ButtonStyle.green, row=0)
        async def ajout1000(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await self.update(1000, interaction)
    
    @bot.slash_command()
    async def collecte(ctx: disnake.CommandInteraction,
                       item: str,
                       objectif: int):
        """Créé un événement
    
           Parameters
           ----------
           item: Item désiré
           objectif: Qauntité totale désirée
        """
        title = f'Collecte de {item}'
        #await ctx.send('coucou', view=ProgressView(objectif=objectif))
        await ctx.send(embed=progress_embed(title, 0, objectif), view=ProgressView(title=title, objectif=objectif))

    async def update_invasion(reaction):
        selected = await reaction.message.reactions[0].users().flatten()
        embed = reaction.message.embeds[-1]
        embed.clear_fields()
        embed.add_field(name="Enregistrés :", value=len(selected)-1, inline=True)
        await reaction.message.edit(embed=embed)
    
    async def check_user_role(reaction, user):
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
    
            await update_invasion(reaction)
    
            await user.edit(nick=df.at[dtag(user), "Pseudo IG"])
            if role is None:
                # Make sure the role still exists and is valid.
                return
            try:
                # Finally, add the role.
                await user.add_roles(role)
            except disnake.HTTPException:
                # If we want to do something in case of errors we'd do it here.
                ...
    def instance_data(reaction):
        fields = {e.name: e.value.split('\n') for e in reaction.message.embeds[-1].fields}
        return fields['Rôles'], fields['Joueurs']
    
    async def update_instance_embed(reaction, roles, joueurs):
        # Récupération et mise à jour du message initial
        embed = reaction.message.embeds[-1]
        embed.clear_fields()
        embed.add_field(name="Rôles", value=list_to_field(roles), inline=True)
        embed.add_field(name="Joueurs", value=list_to_field(joueurs), inline=True)
        await reaction.message.edit(embed=embed)
    
    async def update_instance(reaction, user, add=True):
        message = reaction.message
        cmd_author = message.interaction.user
    
        roles, joueurs = instance_data(reaction)
    
        if reaction.emoji == '✅':
            if user == cmd_author:
                # Create vocal and swap users
    
                categories = message.guild.categories
                category = disnake.utils.find(lambda c: c.id == 948167052722573322, categories)
                voice = await category.create_voice_channel(f'Instance de {user.display_name}')
    
                ids = [int(re.sub("[^0-9]", "", j)) for j in joueurs if j != 'libre']
    
                users = await message.guild.getch_members(ids)
    
                for u in users:
                    if u.voice:
                        await u.move_to(voice)
                    else:
                        invite = await voice.create_invite()
                        await u.send(f"L'instance a démarré, rejoins ici : {invite} ", embed=message.embeds[-1])
                await message.delete(delay=60)
                return
    
        if reaction.emoji == '❌':
            if user == cmd_author:
                await message.delete()
            return
    
        if user.mention not in joueurs:
            for i, r in enumerate(roles):
                if reaction.emoji == r and joueurs[i] == 'libre':
                    joueurs[i] = user.mention
                    break
    
        await update_instance_embed(reaction, roles, joueurs)
    async def update_instance_rm(reaction, user):
        roles, joueurs = instance_data(reaction)
        # Le joueur est-il séléctionné ?
        if user.mention in joueurs:
            # On le supprime de la liste des joueurs en le remplacant par libre
            for i, r in enumerate(roles):
                if joueurs[i] == user.mention and r==reaction.emoji:
                    joueurs[i] = 'libre'
                    break
    
            for i, r in enumerate(roles):
                if joueurs[i] == 'libre':
                    disponibles = [d for d in reaction.message.reactions if d.emoji == r][-1]
                    # On récupére les utilisateurs en prennat soint de filtrer le bot
                    disponibles = [u for u in await disponibles.users().flatten() if u != bot.user and u.mention not in joueurs]
                    if disponibles:
                        joueurs[i] = disponibles[0].mention
    
        await update_instance_embed(reaction, roles, joueurs)
    
    @bot.event
    async def on_reaction_add(reaction, user):
         if user == bot.user:
             return
         if not reaction.message.embeds:
             return
         msg_type = reaction.message.embeds[-1].footer.text
    
         if msg_type == 'Invasion':
             await check_user_role(reaction, user)
             return
         if msg_type == 'Instance':
             await update_instance(reaction, user)
             return
    
    @bot.event
    async def on_reaction_remove(reaction, user):
         if user == bot.user:
             return
         if not reaction.message.embeds:
             return
         msg_type = reaction.message.embeds[-1].footer.text
         if msg_type == 'Invasion':
             await update_invasion(reaction)
             return
         if msg_type == 'Instance':
             await update_instance_rm(reaction, user)
             return
    
    @bot.event
    async def on_voice_state_update(member, before, after):
        instances_cat = 948167052722573322
        invasions_cat = 906648457824051252
        to_purge = [instances_cat, invasions_cat]
    
        invasions_waiting = 948204662086058076
        instances_waiting = 948198317983146034
        protected = [invasions_waiting, instances_waiting]
        if before.channel and before.channel.category_id in to_purge:
            if not before.channel.members and before.channel.id not in protected:
                await before.channel.delete()
    bot.run(token=open("bot.token").read()[:-1])

if __name__ == "__main__":
    main()
