import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

def get_test_roster():
    page= 'Roster'
    url = f"https://docs.google.com/spreadsheets/d/1FgtMvUQbLxP7qvXt2tnVwFFyX9KWnuREHu7o0RtX13M/gviz/tq?tqx=out:csv&sheet={page}"
    #return pd.read_csv(url).iloc[:, 0:16].dropna().set_index('dtag')
    return pd.read_csv(url).set_index('dtag')

def get_test_strat():
  page= 'Strat'
  url = f"https://docs.google.com/spreadsheets/d/1vDZ_p6Bq2oyyY0CV1SQ0FBRtJoGbtiurM9cOQWHJ-qo/gviz/tq?tqx=out:csv&sheet={page}"
  return pd.read_csv(url).iloc[0:5, 0:12]

def build_comp(roster, strat, config):
    roles = {}
    for index, row in strat.iterrows():
        for v in row:
            v = v.split(' ')[0]
            if v in roles:
                roles[v] += 1
            else:
                roles[v] = 1

    max_roles = {k: v.max() for k,v in roster.iteritems()}
    
    cols = [k for k, v in roles.items() for _ in range(v)]
    rows = roster.index
    
    C = np.zeros((len(rows), len(cols)), dtype=int)
    
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            C[i, j] = roster.at[r, c]
    
    row_ind, X = linear_sum_assignment(C, maximize=True)
    score = C[row_ind, X].sum()
    assignent = {p: cols[t] for p, t in zip(rows, X)}
    
    filed_roles = {}
    for k, v in assignent.items():
        #print(k, v)
        if v not in filed_roles:
            filed_roles[v] = [k]
        else:
            filed_roles[v] += [k]
    
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

if __name__ == '__main__':
    roster = get_test_roster().set_index('Pseudo IG')
    roster.to_csv('roster.csv')
    print(roster)
    strat = get_test_strat()
    strat.to_csv('strat.csv')
    print(strat)
    print(build_comp(roster, strat))
