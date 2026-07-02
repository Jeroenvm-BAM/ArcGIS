# export_project_layers.py
# Exporteert alle gewenste featurelagen uit een webmap binnen een specifieke groep
# Combineert alles in één TXT-bestand met komma's als scheidingsteken
# X,Y,Z afgerond op 2 decimalen

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import os
import sys
import pandas as pd

# ===================== CONFIGURATIE =====================
PORTAL_URL = "https://www.arcgis.com"           # of je eigen portal URL

OUTPUT_FOLDER = r"C:\GIS\Download"

# Welke lagen wil je hebben? (substring match, case-insensitive)
DESIRED_LAYERS = ["Inmeet", "Uitzet", "Weg", "Put", "Water", "Bodem"]

# Welke velden wil je exporteren (hoofdlettergevoelig!)
GEWENSTE_KOLOMMEN = ["ID", "X", "Y", "Z"]

# Naam van de groep waarin de webmap(pen) zich bevinden
GROUP_NAME = "Bodem_9350"                       # pas eventueel aan

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def find_group_by_title(gis, group_title):
    """Zoek een groep op titel"""
    try:
        groups = gis.groups.search(f'title:"{group_title}"', max_groups=10)
        if not groups:
            return None
        
        # Probeer exacte match
        exact = [g for g in groups if g.title.strip().lower() == group_title.strip().lower()]
        if exact:
            return exact[0]
        
        # Anders eerste match
        return groups[0]
    except Exception as e:
        print(f"Fout bij zoeken naar groep: {e}")
        return None


def extract_operational_layers(webmap_data):
    """Recursief alle operationele lagen verzamelen, inclusief sublagen in groepen"""
    layers = []

    def recurse(item):
        if isinstance(item, dict):
            if 'layerType' in item and item['layerType'] in ['ArcGISFeatureLayer', 'GroupLayer']:
                if 'title' in item:
                    layers.append(item)
                if 'layers' in item:
                    for sub in item['layers']:
                        recurse(sub)
            elif 'layers' in item:
                for sub in item['layers']:
                    recurse(sub)
        elif isinstance(item, list):
            for sub in item:
                recurse(sub)

    if 'operationalLayers' in webmap_data:
        for op_layer in webmap_data['operationalLayers']:
            recurse(op_layer)

    return layers


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python export_project_layers.py <projectnummer>")
        print("Voorbeeld: python export_project_layers.py \"COP.26010.01.32\"")
        sys.exit(1)

    projectnummer = sys.argv[1].strip()
    print("=" * 70)
    print(f"Project: {projectnummer}")
    print(f"Zoeken in groep: {GROUP_NAME}")
    print("Exporteren → één gecombineerd TXT (X/Y/Z op 2 decimalen)")
    print("=" * 70)

    # Verbinden met ArcGIS (via ArcGIS Pro profiel)
    try:
        gis = GIS("pro")
        if gis.users.me is None:
            print("FOUT: Geen actieve login gevonden in ArcGIS Pro.")
            sys.exit(1)
        print(f"Ingelogd als: {gis.users.me.username}")
    except Exception as e:
        print(f"VERBINDING MISLUKT: {e}")
        sys.exit(1)

    # Groep vinden
    group = find_group_by_title(gis, GROUP_NAME)
    if not group:
        print(f"Geen groep gevonden met titel '{GROUP_NAME}'.")
        sys.exit(1)

    print(f"Groep gevonden: {group.title} (ID: {group.id})")

    # Webmap zoeken BINNEN de groep
    search_query = f'group:"{group.id}" title:"{projectnummer}" type:"Web Map"'
    items = gis.content.search(query=search_query, max_items=5)

    if not items:
        print(f"Geen webmap gevonden met titel '{projectnummer}' in groep '{GROUP_NAME}'.")
        # Alternatieve poging zonder aanhalingstekens rond titel
        print("Probeer bredere zoekopdracht...")
        search_query = f'group:"{group.id}" {projectnummer} type:"Web Map"'
        items = gis.content.search(query=search_query, max_items=5)

    if not items:
        print("Geen webmap gevonden. Controleer titel en groep.")
        sys.exit(1)

    webmap_item = items[0]
    print(f"Webmap gevonden: {webmap_item.title} (ID: {webmap_item.id})")

    # Webmap JSON ophalen
    try:
        webmap_data = webmap_item.get_data()
        if not webmap_data:
            print("Web map data is leeg.")
            sys.exit(1)
    except Exception as e:
        print(f"Fout bij ophalen webmap JSON: {e}")
        sys.exit(1)

    # Lagen verzamelen
    op_layers = extract_operational_layers(webmap_data)

    if not op_layers:
        print("Geen operationele lagen gevonden in de webmap.")
        sys.exit(1)

    print(f"Aantal gevonden lagen/groepen: {len(op_layers)}")

    all_data = []
    exported = 0

    for layer_def in op_layers:
        title = layer_def.get('title', 'Onbekend').strip()
        url = layer_def.get('url', '')

        if not url or 'FeatureServer' not in url:
            continue

        title_lower = title.lower()
        matched = any(d.lower() in title_lower for d in DESIRED_LAYERS)
        if not matched:
            continue

        print(f"Verwerken laag: {title} (URL: {url})")

        try:
            fl = FeatureLayer(url, gis=gis)

            df = fl.query(
                as_df=True,
                return_geometry=False,
                out_fields="*"
            )

            # Alleen gewenste kolommen houden (indien aanwezig)
            beschikbare = [kolom for kolom in GEWENSTE_KOLOMMEN if kolom in df.columns]
            if beschikbare:
                df = df[beschikbare]
            else:
                print("   Waarschuwing: geen van de gewenste kolommen gevonden → sla over of pas GEWENSTE_KOLOMMEN aan")

            # OBJECTID verwijderen als aanwezig
            for oid in ['OBJECTID', 'objectid']:
                if oid in df.columns:
                    df = df.drop(columns=[oid])

            # X,Y,Z afronden op 2 decimalen
            for col in ['X', 'Y', 'Z']:
                if col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
                    except:
                        pass

            # Komma → punt (voor de zekerheid)
            for col in ['X', 'Y', 'Z']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)

            if len(df) > 0:
                all_data.append(df)
                exported += 1
                print(f"   → toegevoegd ({len(df)} rijen)")
            else:
                print("   → geen rijen in deze laag")

        except Exception as e:
            print(f"   Fout bij laag {title}: {e}")

    # Alles combineren en exporteren
    print("\n" + "=" * 70)

    if exported > 0 and all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Volgorde behouden zoals in GEWENSTE_KOLOMMEN
        cols = [c for c in GEWENSTE_KOLOMMEN if c in combined_df.columns]
        if cols:
            combined_df = combined_df[cols]

        output_file = os.path.join(OUTPUT_FOLDER, f"{projectnummer.replace('.', '_')}_alle_lagen.txt")

        combined_df.to_csv(
            output_file,
            sep=',',
            decimal='.',
            index=False,
            encoding='utf-8-sig'
        )

        print(f"Klaar! {exported} lagen gecombineerd in:")
        print(f"→ {output_file}")
        print(f"Totaal rijen: {len(combined_df)}")
        print(f"Kolommen: {list(combined_df.columns)}")
    else:
        print("Geen bruikbare data gevonden of geen lagen succesvol verwerkt.")

    print("=" * 70)


if __name__ == "__main__":
    main()