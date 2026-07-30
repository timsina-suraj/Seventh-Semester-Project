// Mirrors app/models/nepal_locations.py in the backend — keep both in sync.
// District spellings match the ML pipeline's climate dataset wherever that
// dataset covers the district; see the backend module for the full note.

export const DISTRICTS_BY_PROVINCE = {
  Koshi: [
    "Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang",
    "Okhaldhunga", "Panchther", "Sankhuwasabha", "Solukhumbu",
    "Sunsari", "Taplejung", "Terhathum", "Udayapur",
  ],
  Madhesh: [
    "Bara", "Dhanusa", "Mahottari", "Parsa", "Routahat",
    "Saptari", "Sarlahi", "Siraha",
  ],
  Bagmati: [
    "Bhaktapur", "Chitawan", "Dhading", "Dolkha", "Kathmandu",
    "Kabhre", "Lalitpur", "Makwanpur", "Nuwakot", "Ramechhap",
    "Rasuwa", "Sindhuli", "Sindhupalchok",
  ],
  Gandaki: [
    "Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang",
    "Myagdi", "Nawalpur", "Parbat", "Syangja", "Tanahun",
  ],
  Lumbini: [
    "Arghakhanchi", "Banke", "Bardiya", "Dang", "Rukum East",
    "Gulmi", "Kapilvastu", "Parasi", "Palpa", "Pyuthan",
    "Rolpa", "Rupandehi",
  ],
  Karnali: [
    "Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot",
    "Mugu", "Salyan", "Surkhet", "Rukum West",
  ],
  Sudurpashchim: [
    "Achham", "Baitadi", "Bajang", "Bajura", "Dadeldhura",
    "Darchula", "Doti", "Kailali", "Kanchanpur",
  ],
};

export const PROVINCES = Object.keys(DISTRICTS_BY_PROVINCE);

export const DISTRICTS = Object.values(DISTRICTS_BY_PROVINCE).flat().sort((a, b) => a.localeCompare(b));
