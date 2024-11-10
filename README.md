# ecquote

A package to estimate the cost and volume of an ECMWF dissemination feed based on the rules described [there](https://www.ecmwf.int/en/forecasts/accessing-forecasts/payment-rules-and-options/tariffs).

To use the tool, edit a file that contains the
a series of [MARS requests](https://confluence.ecmwf.int/display/UDOC/MARS+command+and+request+syntax) as follows:

    class=od,
    stream=oper,
    expver=0001,
    levtype=pl,
    type=an,
    time=0000/1200,
    param=z/t/u/v,
    levelist=500/850,
    grid=0.1/0.1,
    area=40/0/30/50

    type=fc,
    step=0/to/240/by/24

    type=cf,
    stream=enfo

    type=pf,
    number=1/to/50

The verb of the request, such as `retrieve` or `dissemination`, is optional. The example above describes four requests. As for with the MARS language, attributes that are not specified are inherited from the previous request.

Then simply run the `ecquote` tools:

    ecquote myrequests.req

You then should get a result such as:

    Grand total:

        Yearly volume:    256.9 GiB
        Yearly fields:    3,346,320
        Volume band:      1 GiB
        Volume cost:      EUR 200
        EPUs:             16,627
        Discounted EPUs:  10,776
        Information cost: EUR 5,388 (core: 5,388)

To get a description of how the cost is determined, rerun the command with the option `--detailed`.

# Conditions of use

This tool is provided for evaluation and review purchases only.  Only quotes submitted via the Product Requirements Catalogue will be reviewed/considered/approved:  https://apps.ecmwf.int/shopping-cart/

# Licence

Copyright 2024 European Centre for Medium-Range Weather Forecasts (ECMWF).

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
