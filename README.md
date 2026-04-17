## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```


## Run tests
```bash
python -m pytest
```


## Pricing rules

### By size

| Type   | Max dimension | Price |
|--------|-------------|-------|
| Small  | < 10 cm     | $3    |
| Medium | < 50 cm     | $8    |
| Large  | < 100 cm    | $15   |
| XL     | >= 100 cm   | $25   |

### By weight

Each parcel type has a weight limit. Parcels exceeding the limit incur an additional $2/kg.

| Type   | Weight limit |
|--------|-------------|
| Small  | 1 kg        |
| Medium | 3 kg        |
| Large  | 6 kg        |
| XL     | 10 kg       |

### Speedy shipping

When `speedy=True` is selected, the total order cost is doubled. The base parcel costs remain unchanged; the extra $2/kg weight charge still applies per parcel. The speedy shipping cost is listed as a separate item in the result.

