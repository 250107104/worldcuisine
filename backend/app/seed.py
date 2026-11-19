"""Reference metadata for countries supported by TheMealDB and a demo account."""
from app.db import Store, utcnow

# TheMealDB exposes cuisine areas (e.g. "Italian"), not country records. This small
# mapping supplies stable URL ids and ISO codes while dishes remain sourced upstream.
COUNTRIES = [
    ("italy", "it", "ITA", "Italy", "Italian"), ("japan", "jp", "JPN", "Japan", "Japanese"),
    ("mexico", "mx", "MEX", "Mexico", "Mexican"), ("india", "in", "IND", "India", "Indian"),
    ("france", "fr", "FRA", "France", "French"), ("thailand", "th", "THA", "Thailand", "Thai"),
    ("turkey", "tr", "TUR", "Turkey", "Turkish"), ("morocco", "ma", "MAR", "Morocco", "Moroccan"),
    ("china", "cn", "CHN", "China", "Chinese"), ("usa", "us", "USA", "United States", "American"),
    ("greece", "gr", "GRC", "Greece", "Greek"), ("spain", "es", "ESP", "Spain", "Spanish"),
    ("uk", "gb", "GBR", "United Kingdom", "British"), ("vietnam", "vn", "VNM", "Vietnam", "Vietnamese"),
    ("egypt", "eg", "EGY", "Egypt", "Egyptian"), ("canada", "ca", "CAN", "Canada", "Canadian"),
    ("kenya", "ke", "KEN", "Kenya", "Kenyan"), ("uruguay", "uy", "URY", "Uruguay", "Uruguayan"),
    ("croatia", "hr", "HRV", "Croatia", "Croatian"), ("netherlands", "nl", "NLD", "Netherlands", "Dutch"),
    ("philippines", "ph", "PHL", "Philippines", "Filipino"), ("ireland", "ie", "IRL", "Ireland", "Irish"),
    ("jamaica", "jm", "JAM", "Jamaica", "Jamaican"), ("malaysia", "my", "MYS", "Malaysia", "Malaysian"),
    ("poland", "pl", "POL", "Poland", "Polish"), ("portugal", "pt", "PRT", "Portugal", "Portuguese"),
    ("russia", "ru", "RUS", "Russia", "Russian"), ("tunisia", "tn", "TUN", "Tunisia", "Tunisian"),
    ("ukraine", "ua", "UKR", "Ukraine", "Ukrainian"),
]


def load_seed(store: Store) -> None:
    """Load stable country metadata and a demo user; never seed dishes locally."""
    for cid, iso2, iso3, name, cuisine in COUNTRIES:
        store.countries[cid] = {"id": cid, "iso2": iso2, "iso3": iso3, "name": name, "cuisine": cuisine}
    uid = store.next_id("user")
    store.users[uid] = {"id": uid, "username": "Food Explorer", "bio": "", "avatar": "🍜", "created_at": utcnow()}
    store.init_user_data(uid)
