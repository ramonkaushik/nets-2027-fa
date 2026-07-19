import re
import unicodedata


def normalize_name(name: str) -> str:
    """Lowercase ASCII, strip name suffixes (Jr/Sr/II/III/IV) and extra whitespace.

    Used to match player names across NBA.com, Basketball Reference, and Spotrac,
    which all format names slightly differently.
    """
    nfkd = unicodedata.normalize('NFKD', str(name))
    ascii_ = nfkd.encode('ascii', 'ignore').decode()
    ascii_ = re.sub(r"\b(jr|sr|ii|iii|iv)\.?", '', ascii_, flags=re.IGNORECASE)
    return ' '.join(ascii_.lower().split())
