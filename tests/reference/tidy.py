#!/usr/bin/env python3
import sys

from ecquote.cart import Cart
from ecquote.utils import as_numbers

for path in sys.argv[1:]:
    print(path)
    cost = {}
    with open(path) as f:
        for line in f:
            if line.startswith("# "):
                if "=" in line:
                    key, value = line[2:].strip().split("=")
                    cost[key.strip()] = as_numbers(value.strip())

    cart = Cart.from_request_files(path, inherit=True)

    with open(path, "w") as f:
        for k, v in sorted(cost.items()):
            print(f"# {k}={v}", file=f)
        print(file=f)
        cart.dump_requests(file=f)
