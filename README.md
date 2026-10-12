# FORC, magnetic hysteresis and FMR publication counts, 1991–2025

openalex_output_counts.py is a Python script that counts papers from 1991 to 2025 in [OpenAlex](https://openalex.org) that mention one of three techniques in their title or abstract. The techniques are first-order reversal curves (FORC), magnetic hysteresis and ferromagnetic resonance (FMR). Each one is counted three ways:

- **all**: every matching paper.
- **NERC-remit**: the title or abstract also contains an earth or environmental science term, such as palaeomagnetism, sediment, soil, magnetotactic, volcanic or pollution. This is a keyword stand-in, not an official NERC classification.
- **NERC-funded**: OpenAlex links the paper to the Natural Environment Research Council as a funder (funder ID `F4320334631`). Funding records are incomplete, so treat this as a minimum.


## Requirements

You need Python 3.8 or later and nothing else, since the script uses only the standard library.

## Usage

```sh
export OPENALEX_API_KEY=...          # free key; anonymous use has a small shared daily budget
python3 openalex_output_counts.py           # writes results_<date>/{by_year,summary}.csv + queries.json
python3 openalex_output_counts.py --dump-ids   # also saves the matching work IDs + DOIs per query
```

Summary output from the 12 October 2026 run:

```
technique	subset	total_1991_2025	1991-95	1996-00	2001-05	2006-10	2011-15	2016-20	2021-25
FORC	all	1317	3	8	88	180	279	353	406
FORC	remit	281	0	1	16	32	62	76	94
FORC	nerc_funded	28	0	0	2	3	8	9	6
Hysteresis	all	41770	2382	3250	4983	6089	7757	8584	8725
Hysteresis	remit	1626	99	133	203	187	258	312	434
Hysteresis	nerc_funded	47	3	4	0	6	14	7	13
FMR	all	10098	514	628	1052	1550	1899	2271	2184
FMR	remit	152	16	11	18	22	34	26	25
FMR	nerc_funded	1	0	0	0	0	1	0	0
```

OpenAlex is continually updated, so later runs may give slightly different numbers.


## Definitions

All searches use `title_and_abstract.search`, which matches stemmed words or phrases in the title and abstract. Year range is `publication_year:2001-2025`.

| Technique | Search expression |
|---|---|
| FORC | `"first order reversal curve" OR "FORC diagram" OR "FORC distribution"` |
| Magnetic hysteresis | `hysteresis AND (magnetic OR magnetization OR magnetisation)` |
| FMR | `"ferromagnetic resonance"` |

| Subset | Extra filter |
|---|---|
| `all` | none |
| `remit` (NERC-remit proxy) | the title or abstract also contains one of: paleo/palaeomagnetism/-ic, "rock magnetic/magnetism", "environmental magnetism", "mineral magnetism", geomagnetic, sediment, soil, rock, basalt, meteorite, magnetotactic, geological, loess, volcanic, marine, lake, atmospheric, pollution, dust, particulate |
| `nerc_funded` | `funders.id:F4320334631` (Natural Environment Research Council, GB) |


## Caveats

- On its own, bare "FORC" matches unrelated acronyms (for example in biology), so this is left out of the search.
- OpenAlex's topic classification puts most rock magnetism papers under Physics or Materials. Filtering on the Earth and Planetary Sciences or Environmental Science fields give only a limited number of FORC papers, so the remit subset uses keywords instead.
- Funder metadata is sparse before about 2010 and is never complete. Treat `nerc_funded` as a lower bound.
- These counts are papers that mention the technique in the title or abstract. Papers that use it only in the methods section are missed.


## Getting an API key

The script works without a key, but you're then sharing a small daily allowance with everyone on the same network. Once that runs out, requests fail with `HTTP Error 429: Too Many Requests`. A free key gives you 10 times as much ([OpenAlex authentication docs](https://help.openalex.org/api/authentication/)).

1. Create a free account at [openalex.org](https://openalex.org). No payment details are needed.
2. Copy your key from [openalex.org/settings/api](https://openalex.org/settings/api).
3. Export it before running the script, or add the line to `~/.zshrc`:

   ```sh
   export OPENALEX_API_KEY=your_key
   ```

See [OpenAlex pricing](https://help.openalex.org/access/pricing/) for information on usage limits.
