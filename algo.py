# Licence

# [[file:readme.org::*Licence][Licence:1]]
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
# Licence:1 ends here

# Dépendances

# [[file:readme.org::*Dépendances][Dépendances:1]]
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from typing import Dict, List, Tuple
import numpy.typing as npt

NDArrayInt = npt.NDArray[np.int_]
# Dépendances:1 ends here

# Données de test

# [[file:readme.org::*Données de test][Données de test:1]]
def get_test_roster():
    url = "https://docs.google.com/spreadsheets/d/1FgtMvUQbLxP7qvXt2tnVwFFyX9KWnuREHu7o0RtX13M/gviz/tq?tqx=out:csv&sheet=Roster"
    return pd.read_csv(url).set_index('dtag')
# Données de test:1 ends here

# [[file:readme.org::*Données de test][Données de test:2]]
def get_test_strat():
    url = "https://docs.google.com/spreadsheets/d/1FgtMvUQbLxP7qvXt2tnVwFFyX9KWnuREHu7o0RtX13M/gviz/tq?tqx=out:csv&sheet=Strat_principale"
    page = pd.read_csv(url)
    return page.iloc[0:5, 0:10]
# Données de test:2 ends here

# Identification des rôles à attribuer

# La première étape consiste à extraire, depuis la stratégie d'entrée,
# les rôles à attribuer.


# [[file:readme.org::*Identification des rôles à attribuer][Identification des rôles à attribuer:1]]
def extraction_roles(strat: pd.DataFrame) -> Dict[str, int]:
    roles = {}
    for index, row in strat.iterrows():
        for v in row:
            v = v.split(' ')[0]
            if v in roles:
                roles[v] += 1
            else:
                roles[v] = 1
    return roles
# Identification des rôles à attribuer:1 ends here

# Matrice de coûts
# Maintenant que les rôles sont déterminés, l'objectif est d'affecter
# pour chacun un joueur. C'est un classique d'optimisation combinatoire,
# connu sous le terme de problème d'[[https://en.wikipedia.org/wiki/Assignment_problem][affectation]].

# La programmation linéaire est une technique éprouvée pour résoudre ce
# problème. L'idée est de représenter le problème par une matrice $C$ de
# pertinence (ou de coût si minimisation), où chaque élément $C_{i,j}$
# représente la pertinence d'attribuer le rôle $i$ au joueur $j$.

# Nous avons besoin de créer la matrice $C$ ainsi que des labels de
# lignes /rows/ et de colonnes /cols/ faisant le lien entre les index
# $i$ et $j$ et les noms de rôles/joueurs.

#  #+name: cout

# [[file:readme.org::cout][cout]]
def matrice_cout(roles: pd.DataFrame, roster: pd.DataFrame) -> Tuple[List[str], List[str], NDArrayInt]:
    cols = [k for k, v in roles.items() for _ in range(v)]
    rows = roster.index

    C = np.zeros((len(rows), len(cols)), dtype=int)

    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            #print(roster.at[r, c])
            C[i, j] = int(roster.at[r, c])
    return rows, cols, C
# cout ends here

# Résolution
# Puis, il faut trouver la matrice d'assignation $X$ qui va maximiser la
# pertinence totale de la manière suivante :

# $$max \sum_{i} \sum_{j} C_{i,j} X_{i,j}$$

# Nous utiliserons pour cela la fonction [[https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html][linear_sum_assignment]] de
# [[https://docs.scipy.org/doc/scipy/index.html][Scipy]]. Ensuite, nous créons un dictionnaire avec les assignations
# choisies.


# [[file:readme.org::*Résolution][Résolution:1]]
def solve(rows: List[str], cols: List[str], C: NDArrayInt) -> Dict[str, str]:
    row_ind, X = linear_sum_assignment(C, maximize=True)
    # score = C[row_ind, X].sum()
    return {p: cols[t] for p, t in zip(rows, X)}
# Résolution:1 ends here

# Exploitation des résultats
# Remplissage de la composition des groupes en fonciton des assignations
# calculées.

# [[file:readme.org::*Exploitation des résultats][Exploitation des résultats:1]]
def creation_compo(assignations: Dict[str, str], roster: pd.DataFrame) -> pd.DataFrame:
    filed_roles = {}
    for k, v in assignations.items():
        if v not in filed_roles:
            filed_roles[v] = [k]
        else:
            filed_roles[v] += [k]

    max_roles = {k: v.max() for k,v in roster.iteritems()}

    comp = strat.copy()
    for i, row in comp.iterrows():
        for j, v in row.items():
            label = ''
            if len(v.split(' ')) > 1:
                v, label = v.split(' ')
            if v in filed_roles and filed_roles[v]:
                p = filed_roles[v].pop()
                role_txt = f"[{comp.at[i, j]}]({config['doc']['url']})"
                #if role_txt in config['doc']:
                #    role_txt = f"[{role_txt}]({config['doc'][url]})"
                comp.at[i, j] = f'{p} *{role_txt}* {roster.at[p, v] / max_roles[v]:.1f}'
    return comp
# Exploitation des résultats:1 ends here

# Processus complet

# [[file:readme.org::*Processus complet][Processus complet:1]]
def build_comp(roster: pd.DataFrame, strat: pd.DataFrame, config):
    roles = extraction_roles(strat)
    print(roles)
    assignation = solve(*matrice_cout(roles, roster))
    return creation_compo(assignation, roster)
# Processus complet:1 ends here

# Test algorithme


# [[file:readme.org::*Test algorithme][Test algorithme:1]]
import json
with open('config.json', 'r') as datafile:
    config = json.load(datafile)
if __name__ == '__main__':
    with open('config.json', 'r') as datafile:
        config = json.load(datafile)
    roster = get_test_roster()
    roster.to_csv('roster.csv')
    print(roster)
    strat = get_test_strat()
    strat.to_csv('strat.csv')
    print(strat)
    print(build_comp(roster, strat, config))
# Test algorithme:1 ends here
