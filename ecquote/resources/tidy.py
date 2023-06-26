#!/usr/bin/env python3
import yaml
sets = yaml.safe_load(open('sets.yaml'))

for k,v in sets.items():
    if 'step' in v['mars']:
        v['mars']['step'] = sorted(v['mars']['step'])


print(yaml.dump(sets))
