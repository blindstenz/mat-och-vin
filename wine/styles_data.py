"""Reference list of wine styles.

Pairings point at styles rather than bottles, so suggestions work before the
cellar exists and the cellar match later is a style lookup.

Scales are 1-5. `pairs_with` holds profile keywords (see wine.profile) that the
rules engine rewards; keep them to the keys defined there.
"""

WINE_STYLES = [
    # Mousserande
    dict(key="champagne", name="Champagne / Crémant", colour="sparkling", body=2, acidity=5, tannin=1, sweetness=1,
         grapes="Chardonnay, Pinot Noir, Pinot Meunier", regions="Champagne, Crémant de Bourgogne, Cava",
         pairs_with="shellfish fish fried raw salty cheese creamy"),
    dict(key="prosecco", name="Prosecco", colour="sparkling", body=1, acidity=4, tannin=1, sweetness=2,
         grapes="Glera", regions="Veneto", pairs_with="raw salty fried vegetables"),
    # Vitt, lätt och friskt
    dict(key="sauvignon_blanc", name="Sauvignon Blanc", colour="white", body=2, acidity=5, tannin=1, sweetness=1,
         grapes="Sauvignon Blanc", regions="Loire (Sancerre), Marlborough", pairs_with="fish shellfish vegetables herby citrus cheese raw"),
    dict(key="chablis", name="Chablis / ooxad Chardonnay", colour="white", body=2, acidity=5, tannin=1, sweetness=1,
         grapes="Chardonnay", regions="Chablis, Mâconnais", pairs_with="shellfish fish raw steamed butter"),
    dict(key="riesling_dry", name="Torr Riesling", colour="white", body=2, acidity=5, tannin=1, sweetness=1,
         grapes="Riesling", regions="Mosel, Rheingau, Alsace, Clare Valley", pairs_with="fish shellfish pork poultry citrus asian smoked"),
    dict(key="riesling_offdry", name="Halvtorr Riesling", colour="white", body=2, acidity=5, tannin=1, sweetness=3,
         grapes="Riesling", regions="Mosel, Nahe", pairs_with="spicy asian pork poultry sweet_sour"),
    dict(key="albarino", name="Albariño / Vinho Verde", colour="white", body=2, acidity=5, tannin=1, sweetness=1,
         grapes="Albariño, Loureiro", regions="Rías Baixas, Vinho Verde", pairs_with="shellfish fish grilled citrus raw"),
    dict(key="gruner", name="Grüner Veltliner", colour="white", body=2, acidity=4, tannin=1, sweetness=1,
         grapes="Grüner Veltliner", regions="Wachau, Kamptal", pairs_with="vegetables herby fried pork poultry asian"),
    dict(key="pinot_grigio", name="Pinot Grigio", colour="white", body=2, acidity=3, tannin=1, sweetness=1,
         grapes="Pinot Grigio", regions="Friuli, Alto Adige", pairs_with="fish vegetables pasta"),
    # Vitt, fylligt eller aromatiskt
    dict(key="chardonnay_oaked", name="Ekfatslagrad Chardonnay", colour="white", body=4, acidity=3, tannin=1, sweetness=1,
         grapes="Chardonnay", regions="Bourgogne (Meursault), Kalifornien", pairs_with="creamy butter poultry fish roasted mushrooms shellfish"),
    dict(key="white_burgundy", name="Vit Bourgogne", colour="white", body=3, acidity=4, tannin=1, sweetness=1,
         grapes="Chardonnay", regions="Côte de Beaune", pairs_with="poultry fish creamy butter mushrooms"),
    dict(key="chenin", name="Chenin Blanc", colour="white", body=3, acidity=5, tannin=1, sweetness=2,
         grapes="Chenin Blanc", regions="Vouvray, Savennières, Sydafrika", pairs_with="pork poultry creamy fish sweet_sour"),
    dict(key="gewurztraminer", name="Gewürztraminer", colour="white", body=4, acidity=2, tannin=1, sweetness=2,
         grapes="Gewürztraminer", regions="Alsace", pairs_with="spicy asian cheese aromatic sweet_sour"),
    dict(key="viognier", name="Viognier / vit Rhône", colour="white", body=4, acidity=2, tannin=1, sweetness=1,
         grapes="Viognier, Marsanne, Roussanne", regions="Condrieu, Côtes du Rhône blanc", pairs_with="poultry pork creamy aromatic spicy"),
    # Rosé
    dict(key="rose_provence", name="Torr rosé (Provence)", colour="rose", body=2, acidity=4, tannin=1, sweetness=1,
         grapes="Grenache, Cinsault, Mourvèdre", regions="Provence, Tavel", pairs_with="vegetables fish grilled herby tomato salty"),
    # Rött, lätt
    dict(key="pinot_noir", name="Pinot Noir", colour="red", body=2, acidity=4, tannin=2, sweetness=1,
         grapes="Pinot Noir", regions="Bourgogne, Oregon, Central Otago", pairs_with="poultry mushrooms earthy pork fish game"),
    dict(key="beaujolais", name="Beaujolais / Gamay", colour="red", body=2, acidity=4, tannin=2, sweetness=1,
         grapes="Gamay", regions="Beaujolais (Morgon, Fleurie)", pairs_with="pork poultry charcuterie vegetables"),
    # Rött, medium
    dict(key="chianti", name="Chianti / Sangiovese", colour="red", body=3, acidity=5, tannin=3, sweetness=1,
         grapes="Sangiovese", regions="Toscana", pairs_with="tomato pasta beef herby grilled"),
    dict(key="barbera", name="Barbera", colour="red", body=3, acidity=5, tannin=2, sweetness=1,
         grapes="Barbera", regions="Piemonte", pairs_with="tomato pasta pork charcuterie"),
    dict(key="rioja", name="Rioja / Tempranillo", colour="red", body=3, acidity=3, tannin=3, sweetness=1,
         grapes="Tempranillo, Garnacha", regions="Rioja, Ribera del Duero", pairs_with="lamb pork roasted grilled smoked"),
    dict(key="cotes_du_rhone", name="Côtes du Rhône / Grenache", colour="red", body=3, acidity=3, tannin=3, sweetness=1,
         grapes="Grenache, Syrah, Mourvèdre", regions="Södra Rhône", pairs_with="lamb braised herby roasted"),
    dict(key="merlot", name="Merlot", colour="red", body=3, acidity=3, tannin=3, sweetness=1,
         grapes="Merlot", regions="Bordeaux högra stranden, Chile", pairs_with="beef pork roasted mushrooms"),
    # Rött, fylligt
    dict(key="northern_rhone_syrah", name="Syrah (norra Rhône)", colour="red", body=4, acidity=4, tannin=4, sweetness=1,
         grapes="Syrah", regions="Crozes-Hermitage, Saint-Joseph, Cornas", pairs_with="lamb game grilled herby peppery smoked"),
    dict(key="shiraz", name="Shiraz", colour="red", body=5, acidity=3, tannin=4, sweetness=1,
         grapes="Shiraz", regions="Barossa, McLaren Vale", pairs_with="beef grilled smoked bbq peppery"),
    dict(key="cabernet", name="Cabernet Sauvignon / Bordeaux", colour="red", body=5, acidity=4, tannin=5, sweetness=1,
         grapes="Cabernet Sauvignon, Merlot", regions="Bordeaux vänstra stranden, Napa", pairs_with="beef lamb grilled roasted"),
    dict(key="malbec", name="Malbec", colour="red", body=4, acidity=3, tannin=4, sweetness=1,
         grapes="Malbec", regions="Mendoza, Cahors", pairs_with="beef grilled bbq smoked"),
    dict(key="nebbiolo", name="Barolo / Nebbiolo", colour="red", body=4, acidity=5, tannin=5, sweetness=1,
         grapes="Nebbiolo", regions="Barolo, Barbaresco", pairs_with="beef braised mushrooms earthy game"),
    dict(key="zinfandel", name="Zinfandel / Primitivo", colour="red", body=5, acidity=2, tannin=3, sweetness=2,
         grapes="Zinfandel, Primitivo", regions="Kalifornien, Puglia", pairs_with="bbq smoked spicy pork beef sweet_sour"),
    dict(key="amarone", name="Amarone / Ripasso", colour="red", body=5, acidity=3, tannin=4, sweetness=2,
         grapes="Corvina", regions="Valpolicella", pairs_with="braised game beef cheese"),
    # Sött och starkvin
    dict(key="sauternes", name="Sauternes / ädelsött", colour="sweet", body=4, acidity=4, tannin=1, sweetness=5,
         grapes="Sémillon, Sauvignon Blanc", regions="Sauternes, Tokaj", pairs_with="dessert cheese blue_cheese fruit"),
    dict(key="moscato", name="Moscato d'Asti", colour="sweet", body=1, acidity=3, tannin=1, sweetness=4,
         grapes="Moscato", regions="Piemonte", pairs_with="dessert fruit"),
    dict(key="port", name="Portvin", colour="fortified", body=5, acidity=2, tannin=3, sweetness=5,
         grapes="Touriga Nacional m.fl.", regions="Douro", pairs_with="dessert chocolate blue_cheese cheese"),
]


def sync_styles(WineStyle):
    """Create or update every style in WINE_STYLES (model passed in so migrations can use it)."""
    for data in WINE_STYLES:
        fields = {k: v for k, v in data.items() if k != "key"}
        WineStyle.objects.update_or_create(key=data["key"], defaults=fields)
