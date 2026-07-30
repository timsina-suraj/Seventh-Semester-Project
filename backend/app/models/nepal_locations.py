"""Canonical province and district names for MediShield.

District spellings match `app/ml/data/dengue_dataset_withclimate.csv` wherever
that dataset has an entry for a district, since the dengue prediction pipeline
looks districts up by exact string match against it. For the districts the
climate dataset does not cover (no historical dengue/climate rows), the
standard official spelling is used instead. Two 2015 district splits
(Nawalparasi -> Nawalpur/Parasi, Rukum -> Rukum East/Rukum West) are recorded
as their modern separate names below; the climate dataset predates that split
and still has a single "Nawalparasi" and a single "Rukum" entry, so those four
new-style names do not have an exact climate-data match yet.
"""

VALID_PROVINCES = (
    "Koshi",
    "Madhesh",
    "Bagmati",
    "Gandaki",
    "Lumbini",
    "Karnali",
    "Sudurpashchim",
)

DISTRICTS_BY_PROVINCE = {
    "Koshi": (
        "Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang",
        "Okhaldhunga", "Panchther", "Sankhuwasabha", "Solukhumbu",
        "Sunsari", "Taplejung", "Terhathum", "Udayapur",
    ),
    "Madhesh": (
        "Bara", "Dhanusa", "Mahottari", "Parsa", "Routahat",
        "Saptari", "Sarlahi", "Siraha",
    ),
    "Bagmati": (
        "Bhaktapur", "Chitawan", "Dhading", "Dolkha", "Kathmandu",
        "Kabhre", "Lalitpur", "Makwanpur", "Nuwakot", "Ramechhap",
        "Rasuwa", "Sindhuli", "Sindhupalchok",
    ),
    "Gandaki": (
        "Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang",
        "Myagdi", "Nawalpur", "Parbat", "Syangja", "Tanahun",
    ),
    "Lumbini": (
        "Arghakhanchi", "Banke", "Bardiya", "Dang", "Rukum East",
        "Gulmi", "Kapilvastu", "Parasi", "Palpa", "Pyuthan",
        "Rolpa", "Rupandehi",
    ),
    "Karnali": (
        "Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot",
        "Mugu", "Salyan", "Surkhet", "Rukum West",
    ),
    "Sudurpashchim": (
        "Achham", "Baitadi", "Bajang", "Bajura", "Dadeldhura",
        "Darchula", "Doti", "Kailali", "Kanchanpur",
    ),
}

VALID_DISTRICTS = tuple(
    district for districts in DISTRICTS_BY_PROVINCE.values() for district in districts
)

assert len(VALID_DISTRICTS) == 77
assert len(VALID_PROVINCES) == 7
