"""Starter data. Countries mirror js/data.js; dishes are a small catalog so the API is usable at once."""
from app.db import Store, utcnow

# (id, iso2, iso3, name, cuisine)
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

# (name, country_id, category, ["ingredient:measure", ...], instructions)
DISHES = [
    ("Spaghetti Carbonara", "italy", "Pasta", ["spaghetti:400 g", "guanciale:150 g", "egg yolks:4", "pecorino romano:50 g", "black pepper:1 tsp"],
     "Boil the spaghetti. Crisp the guanciale, then toss it with the hot pasta, beaten yolks, cheese and pepper off the heat until creamy."),
    ("Margherita Pizza", "italy", "Pizza", ["pizza dough:1 ball", "tomato sauce:100 ml", "mozzarella:125 g", "basil:6 leaves", "olive oil:1 tbsp"],
     "Stretch the dough, spread the sauce, add torn mozzarella and bake very hot until blistered. Finish with basil and oil."),
    ("Chicken Teriyaki", "japan", "Chicken", ["chicken thighs:500 g", "soy sauce:60 ml", "mirin:60 ml", "sugar:1 tbsp", "ginger:1 tsp"],
     "Sear the chicken skin-side down, add the sauce mixture and simmer until glossy and sticky. Slice and serve over rice."),
    ("Salmon Sushi Rolls", "japan", "Seafood", ["sushi rice:300 g", "nori sheets:4", "salmon:200 g", "cucumber:1", "rice vinegar:3 tbsp"],
     "Season the cooked rice with vinegar, spread it on nori, add salmon and cucumber, roll tightly and slice."),
    ("Beef Tacos", "mexico", "Beef", ["ground beef:500 g", "taco seasoning:2 tbsp", "corn tortillas:8", "onion:1", "lime:1"],
     "Brown the beef with the seasoning. Warm the tortillas, fill them with beef and onion and squeeze lime over the top."),
    ("Chilaquiles", "mexico", "Breakfast", ["tortilla chips:200 g", "salsa verde:300 ml", "queso fresco:80 g", "egg:2", "cilantro:1 handful"],
     "Simmer the chips in salsa until just softened, top with cheese and fried eggs, and scatter cilantro on top."),
    ("Butter Chicken", "india", "Chicken", ["chicken:600 g", "yogurt:150 g", "tomato puree:300 ml", "butter:50 g", "garam masala:2 tsp", "cream:100 ml"],
     "Marinate and grill the chicken. Simmer tomato puree with butter and spices, stir in cream and add the chicken."),
    ("Chana Masala", "india", "Vegetarian", ["chickpeas:2 cans", "onion:2", "tomato:3", "garam masala:2 tsp", "ginger:1 tbsp"],
     "Fry the onion, ginger and spices, add tomato and chickpeas and simmer until thick and fragrant."),
    ("Coq au Vin", "france", "Chicken", ["chicken legs:6", "red wine:500 ml", "bacon lardons:150 g", "mushrooms:200 g", "pearl onions:12"],
     "Brown the chicken and bacon, then braise slowly in red wine with onions and mushrooms until tender."),
    ("Creme Brulee", "france", "Dessert", ["double cream:500 ml", "egg yolks:5", "sugar:100 g", "vanilla pod:1"],
     "Warm the cream with vanilla, whisk into yolks and sugar, bake gently in a water bath, chill, then caramelise a sugar crust."),
    ("Pad Thai", "thailand", "Seafood", ["rice noodles:200 g", "shrimp:200 g", "tamarind paste:2 tbsp", "peanuts:50 g", "bean sprouts:100 g", "egg:2"],
     "Soak the noodles, stir-fry shrimp and egg, add noodles with tamarind sauce, and finish with sprouts and crushed peanuts."),
    ("Thai Green Curry", "thailand", "Chicken", ["chicken breast:500 g", "green curry paste:3 tbsp", "coconut milk:400 ml", "thai basil:1 handful", "fish sauce:1 tbsp"],
     "Fry the paste, add coconut milk and chicken and simmer. Season with fish sauce and finish with basil."),
    ("Lamb Kofta", "turkey", "Lamb", ["minced lamb:500 g", "onion:1", "parsley:1 bunch", "cumin:1 tsp", "paprika:1 tsp"],
     "Mix everything well, shape onto skewers and grill, turning, until browned and cooked through."),
    ("Chicken Tagine", "morocco", "Chicken", ["chicken thighs:8", "preserved lemon:1", "green olives:100 g", "ras el hanout:2 tsp", "onion:2"],
     "Brown the chicken, add onion, spices and a little water, then cook covered until tender with lemon and olives."),
    ("Kung Pao Chicken", "china", "Chicken", ["chicken breast:400 g", "dried chillies:6", "peanuts:60 g", "soy sauce:2 tbsp", "rice vinegar:1 tbsp"],
     "Stir-fry the chicken with chillies over high heat, add the sauce and peanuts and toss until glazed."),
    ("Apple Pie", "usa", "Dessert", ["apples:6", "pie crust:2 sheets", "sugar:100 g", "cinnamon:1 tsp", "butter:30 g"],
     "Toss sliced apples with sugar and cinnamon, fill the crust, cover with the top sheet and bake until golden."),
    ("Greek Salad", "greece", "Vegetarian", ["tomatoes:4", "cucumber:1", "feta:150 g", "kalamata olives:80 g", "red onion:1", "olive oil:3 tbsp"],
     "Chop the vegetables coarsely, add olives, top with a slab of feta and dress with olive oil and oregano."),
    ("Seafood Paella", "spain", "Seafood", ["paella rice:300 g", "mussels:300 g", "prawns:200 g", "saffron:1 pinch", "chicken stock:900 ml"],
     "Fry the base, stir in rice and saffron stock, arrange the seafood on top and cook without stirring until a crust forms."),
    ("Fish and Chips", "uk", "Seafood", ["cod fillets:4", "flour:150 g", "beer:200 ml", "potatoes:800 g"],
     "Dip the fish in beer batter and deep-fry until crisp, alongside thick-cut chips fried twice."),
    ("Pho Bo", "vietnam", "Beef", ["beef bones:1 kg", "rice noodles:300 g", "star anise:3", "sliced beef:200 g", "fish sauce:2 tbsp"],
     "Simmer the bones with spices for hours, pour the broth over noodles and raw beef slices, and top with herbs."),
    ("Koshari", "egypt", "Vegetarian", ["rice:200 g", "lentils:200 g", "macaroni:150 g", "tomato sauce:300 ml", "fried onions:100 g"],
     "Cook rice, lentils and pasta separately, layer them, then top with spiced tomato sauce and crispy onions."),
    ("Poutine", "canada", "Side", ["french fries:500 g", "cheese curds:200 g", "beef gravy:300 ml"],
     "Pile hot fries with fresh cheese curds and pour hot gravy over so the curds soften."),
    ("Borscht", "ukraine", "Soup", ["beetroot:3", "cabbage:200 g", "potatoes:2", "beef stock:1.5 l", "sour cream:4 tbsp"],
     "Simmer beetroot, cabbage and potatoes in stock until tender and serve topped with sour cream."),
    ("Pierogi Ruskie", "poland", "Side", ["flour:300 g", "potatoes:400 g", "farmer cheese:200 g", "onion:1", "butter:40 g"],
     "Fill rolled dough with mashed potato and cheese, boil until floating, then fry in butter with onion."),
    ("Beef Stroganoff", "russia", "Beef", ["beef strips:500 g", "mushrooms:250 g", "onion:1", "sour cream:150 g", "mustard:1 tsp"],
     "Sear the beef quickly, cook onion and mushrooms, then stir in sour cream and mustard and serve over noodles."),
    ("Pastel de Nata", "portugal", "Dessert", ["puff pastry:1 sheet", "milk:250 ml", "egg yolks:4", "sugar:100 g", "cinnamon:1 stick"],
     "Make a custard with the milk, yolks and sugar, pour into pastry cups and bake very hot until the tops blister."),
    ("Chicken Adobo", "philippines", "Chicken", ["chicken thighs:1 kg", "soy sauce:100 ml", "vinegar:100 ml", "garlic:6 cloves", "bay leaves:3"],
     "Marinate, then simmer the chicken in soy, vinegar and garlic until tender and the sauce reduces."),
]


def load_seed(store: Store) -> None:
    for cid, iso2, iso3, name, cuisine in COUNTRIES:
        store.countries[cid] = {"id": cid, "iso2": iso2, "iso3": iso3, "name": name, "cuisine": cuisine}

    for name, country_id, category, ingredients, instructions in DISHES:
        dish_id = store.next_id("dish")
        store.dishes[dish_id] = {
            "id": dish_id, "name": name, "country_id": country_id, "category": category,
            "tags": [], "image": None, "instructions": instructions, "created_at": utcnow(),
            "ingredients": [{"name": i.split(":")[0], "measure": i.split(":")[1]} for i in ingredients],
        }

    # A ready-to-use demo user so Swagger testing can start immediately.
    uid = store.next_id("user")
    store.users[uid] = {"id": uid, "username": "Food Explorer", "bio": "", "avatar": "🍜", "created_at": utcnow()}
    store.init_user_data(uid)
