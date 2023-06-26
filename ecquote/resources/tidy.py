#!/usr/bin/env python3
import yaml
sets = yaml.safe_load(open('sets.yaml'))


def sort_key(x):
    try:
        return tuple([int(a) for a in x.split('-')])
    except (ValueError, AttributeError):
        return x


for k,v in sets.items():
    for p in v['mars'].keys():
        if isinstance(v['mars'][p], list):
            v['mars'][p] = sorted(set(v['mars'][p]), key=sort_key)




with open('sets.yaml', 'w') as f:
    print(yaml.dump(sets), file=f)
