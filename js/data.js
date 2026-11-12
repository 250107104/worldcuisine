// Country list used by the map and navigation.
// This is configuration, not food data: all dishes and descriptions come from real APIs (see api.js).
//   area -> name of the cuisine/"area" in TheMealDB
//   wiki -> Wikipedia article title for the cuisine description
// Only countries that TheMealDB has dishes for are listed.

export const countries = [
  { id: "italy",   iso3: "ITA", iso2: "it", name: "Italy",          area: "Italian",    wiki: "Italian cuisine" },
  { id: "japan",   iso3: "JPN", iso2: "jp", name: "Japan",          area: "Japanese",   wiki: "Japanese cuisine" },
  { id: "mexico",  iso3: "MEX", iso2: "mx", name: "Mexico",         area: "Mexican",    wiki: "Mexican cuisine" },
  { id: "india",   iso3: "IND", iso2: "in", name: "India",          area: "Indian",     wiki: "Indian cuisine" },
  { id: "france",  iso3: "FRA", iso2: "fr", name: "France",         area: "French",     wiki: "French cuisine" },
  { id: "thailand",iso3: "THA", iso2: "th", name: "Thailand",       area: "Thai",       wiki: "Thai cuisine" },
  { id: "turkey",  iso3: "TUR", iso2: "tr", name: "Turkey",         area: "Turkish",    wiki: "Turkish cuisine" },
  { id: "morocco", iso3: "MAR", iso2: "ma", name: "Morocco",        area: "Moroccan",   wiki: "Moroccan cuisine" },
  { id: "china",   iso3: "CHN", iso2: "cn", name: "China",          area: "Chinese",    wiki: "Chinese cuisine" },
  { id: "usa",     iso3: "USA", iso2: "us", name: "United States",  area: "American",   wiki: "Cuisine of the United States" },
  { id: "greece",  iso3: "GRC", iso2: "gr", name: "Greece",         area: "Greek",      wiki: "Greek cuisine" },
  { id: "spain",   iso3: "ESP", iso2: "es", name: "Spain",          area: "Spanish",    wiki: "Spanish cuisine" },
  { id: "uk",      iso3: "GBR", iso2: "gb", name: "United Kingdom", area: "British",    wiki: "British cuisine" },
  { id: "vietnam", iso3: "VNM", iso2: "vn", name: "Vietnam",        area: "Vietnamese", wiki: "Vietnamese cuisine" },
  { id: "egypt",   iso3: "EGY", iso2: "eg", name: "Egypt",          area: "Egyptian",   wiki: "Egyptian cuisine" },
  { id: "canada",  iso3: "CAN", iso2: "ca", name: "Canada",         area: "Canadian",   wiki: "Canadian cuisine" },
  { id: "kenya",   iso3: "KEN", iso2: "ke", name: "Kenya",          area: "Kenyan",     wiki: "Kenyan cuisine" },
  { id: "uruguay", iso3: "URY", iso2: "uy", name: "Uruguay",        area: "Uruguayan",  wiki: "Uruguayan cuisine" },
  { id: "croatia",     iso3: "HRV", iso2: "hr", name: "Croatia",     area: "Croatian",   wiki: "Croatian cuisine" },
  { id: "netherlands", iso3: "NLD", iso2: "nl", name: "Netherlands", area: "Dutch",      wiki: "Dutch cuisine" },
  { id: "philippines", iso3: "PHL", iso2: "ph", name: "Philippines", area: "Filipino",   wiki: "Filipino cuisine" },
  { id: "ireland",     iso3: "IRL", iso2: "ie", name: "Ireland",     area: "Irish",      wiki: "Irish cuisine" },
  { id: "jamaica",     iso3: "JAM", iso2: "jm", name: "Jamaica",     area: "Jamaican",   wiki: "Jamaican cuisine" },
  { id: "malaysia",    iso3: "MYS", iso2: "my", name: "Malaysia",    area: "Malaysian",  wiki: "Malaysian cuisine" },
  { id: "poland",      iso3: "POL", iso2: "pl", name: "Poland",      area: "Polish",     wiki: "Polish cuisine" },
  { id: "portugal",    iso3: "PRT", iso2: "pt", name: "Portugal",    area: "Portuguese", wiki: "Portuguese cuisine" },
  { id: "russia",      iso3: "RUS", iso2: "ru", name: "Russia",      area: "Russian",    wiki: "Russian cuisine" },
  { id: "tunisia",     iso3: "TUN", iso2: "tn", name: "Tunisia",     area: "Tunisian",   wiki: "Tunisian cuisine" },
  { id: "ukraine",     iso3: "UKR", iso2: "ua", name: "Ukraine",     area: "Ukrainian",  wiki: "Ukrainian cuisine" },
];

export const getCountryById = (id) => countries.find((c) => c.id === id);
export const getCountryByIso3 = (iso3) => countries.find((c) => c.iso3 === iso3);
