"""Recipe profile vocabulary.

A profile describes what matters for wine: the main component, how it is
cooked, the sauce, overall weight and dominant flavours. The keys double as
keywords in WineStyle.pairs_with.
"""

MAIN_COMPONENTS = [
    ("beef", "Nötkött"),
    ("lamb", "Lamm"),
    ("pork", "Fläsk"),
    ("poultry", "Fågel"),
    ("game", "Vilt"),
    ("fish", "Fisk"),
    ("shellfish", "Skaldjur"),
    ("charcuterie", "Chark"),
    ("vegetables", "Grönsaker"),
    ("mushrooms", "Svamp"),
    ("pasta", "Pasta, ris eller pizza"),
    ("cheese", "Ost"),
    ("dessert", "Dessert"),
    ("chocolate", "Choklad"),
]

COOKING_METHODS = [
    ("raw", "Rå"),
    ("steamed", "Ångad eller pocherad"),
    ("fried", "Stekt eller friterad"),
    ("roasted", "Ugnsstekt"),
    ("grilled", "Grillad"),
    ("braised", "Långkok eller gryta"),
    ("smoked", "Rökt"),
]

SAUCES = [
    ("none", "Ingen sås"),
    ("tomato", "Tomat"),
    ("creamy", "Grädde eller ost"),
    ("butter", "Smör"),
    ("asian", "Soja eller asiatisk"),
    ("spicy", "Stark eller chili"),
    ("sweet_sour", "Sötsur"),
    ("citrus", "Citrus"),
    ("bbq", "BBQ"),
]

WEIGHTS = [
    ("light", "Lätt"),
    ("medium", "Mellan"),
    ("heavy", "Mäktig"),
]

FLAVOURS = [
    ("spicy", "Hetta"),
    ("herby", "Örter"),
    ("smoked", "Rök"),
    ("earthy", "Jordigt"),
    ("peppery", "Peppar"),
    ("salty", "Salt"),
    ("citrus", "Syra/citrus"),
    ("aromatic", "Aromatiskt"),
    ("fruit", "Frukt/bär"),
    ("sweet_sour", "Sötsurt"),
    ("blue_cheese", "Blåmögelost"),
]

# Rough body (1-5) that suits each dish weight.
WEIGHT_TO_BODY = {"light": 2, "medium": 3, "heavy": 4.5}

VOCABULARY = {
    key
    for choices in (MAIN_COMPONENTS, COOKING_METHODS, SAUCES, WEIGHTS, FLAVOURS)
    for key, _ in choices
}

LABELS = {
    key: label
    for choices in (MAIN_COMPONENTS, COOKING_METHODS, SAUCES, WEIGHTS, FLAVOURS)
    for key, label in choices
}
