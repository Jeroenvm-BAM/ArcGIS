# -*- coding: utf-8 -*-
import arcpy
from arcgis.gis import GIS

class Toolbox(object):
    def __init__(self):
        self.label = "Field Maps Project Automatisering"
        self.alias = "fieldmaps_project"
        self.tools = [MaakNieuwProject]

class MaakNieuwProject(object):
    def __init__(self):
        self.label = "Maak nieuw Field Maps project (AGOL)"
        self.description = "Maakt een nieuw Field Maps project op basis van een template webmap"
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Projectnummer",
            name="projectnummer",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        p1 = arcpy.Parameter(
            displayName="Projectnaam",
            name="projectnaam",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        return [p0, p1]

    def execute(self, parameters, messages):
        # -------------------------------------------------
        # 1 Projectgegevens
        # -------------------------------------------------
        projectnummer = parameters[0].valueAsText.strip()
        projectnaam = parameters[1].valueAsText.strip()
        folder_name = f"{projectnummer}_{projectnaam}"
        webmap_title = f"{projectnummer}"
        messages.addMessage(f"Start project: {projectnummer} - {projectnaam}")

        # -------------------------------------------------
        # 2 Verbinden met ArcGIS Online
        # -------------------------------------------------
        messages.addMessage("Verbinden met ArcGIS Online...")
        gis = GIS("pro")

        # -------------------------------------------------
        # 3 Projectmap controleren / maken
        # -------------------------------------------------
        folders = gis.content.folders.list()
        folder_names = [f.title for f in folders if hasattr(f, 'title')]
        if folder_name not in folder_names:
            messages.addMessage(f"Map aanmaken: {folder_name}")
            gis.content.create_folder(folder_name)
        else:
            messages.addMessage(f"Map bestaat al: {folder_name}")

        # -------------------------------------------------
        # 4 Template webmap ophalen
        # -------------------------------------------------
        TEMPLATE_WEBMAP_ID = "ea06062f361141c7acb267e6f4b349c9"
        template_item = gis.content.get(TEMPLATE_WEBMAP_ID)
        if not template_item:
            arcpy.AddError("Template webmap niet gevonden.")
            return
        messages.addMessage("Template webmap gevonden")

        # -------------------------------------------------
        # 5 Webmap klonen
        # -------------------------------------------------
        messages.addMessage("Webmap klonen...")
        cloned_items = gis.content.clone_items(
            items=[template_item],
            folder=folder_name,
            copy_data=True,
            search_existing_items=False
        )
        if not cloned_items:
            arcpy.AddError("Klonen mislukt.")
            return

        new_webmap = next((item for item in cloned_items if item.type == "Web Map"), None)
        if not new_webmap:
            arcpy.AddError("Nieuwe webmap niet gevonden.")
            return
        messages.addMessage(f"Nieuwe webmap gemaakt: {new_webmap.title}")

         # -------------------------------------------------
        # 6 Metadata aanpassen (voor ALLE gekloonde items)
        # -------------------------------------------------
        # We maken één gecombineerde tag met de vaste tekst en het nummer
        project_tags = [f"projectnummer:{projectnummer}"]

        for item in cloned_items:
            update_dict = {"tags": project_tags}
            
            if item.type == "Web Map":
                update_dict.update({
                    "title": webmap_title,
                    "snippet": f"Field Maps project {projectnummer}",
                    "description": f"Automatisch aangemaakt Field Maps project: {projectnaam}"
                })
                
            item.update(update_dict)
            
        messages.addMessage("Specifieke projectnummer-tag toegevoegd aan alle gekloonde items.")


        # -------------------------------------------------
        # 7 Groepen ophalen + DEBUG (veilig!)
        # -------------------------------------------------
        messages.addMessage("Groepen ophalen...")
        GROUP_IDS = [
            "3add30df6842406c83dd22ce6592edf3",
            "95aeb21a376a42708f3b6792818cc3bf"
        ]
        target_groups = []
        for gid in GROUP_IDS:
            group = gis.groups.get(gid)
            if not group:
                arcpy.AddWarning(f"Groep niet gevonden: {gid}")
                continue
            messages.addMessage(f"Groep gevonden: {group.title}")
            
            # Veilige toegang - voorkomt KeyError
            try:
                is_shared_update = getattr(group, 'users_update_items', False)
            except Exception:
                is_shared_update = False
            messages.addMessage(f"   → Shared Update groep? {is_shared_update}")

            target_groups.append(group)

        # -------------------------------------------------
        # 8 Items delen met groepen
        # -------------------------------------------------
        if not target_groups:
            arcpy.AddWarning("Geen groepen gevonden → delen overgeslagen")
        else:
            messages.addMessage("Delen met groepen (Shared Update support)...")
            group_ids = [g.id for g in target_groups]

            for item in cloned_items:
                current_shared = item.shared_with
                messages.addMessage(f"{item.title} momenteel: {current_shared}")

                try:
                    success = item.share(
                        groups=",".join(group_ids),
                        allow_members_to_edit=True,
                        everyone=False,
                        org=False
                    )
                    if success and success.get('notSharedWith'):
                        arcpy.AddWarning(f"Probleem delen {item.title}: {success.get('notSharedWith')}")
                    else:
                        messages.addMessage(f"✓ {item.title} gedeeld met groepen")
                except Exception as e:
                    arcpy.AddWarning(f"Fout delen {item.title}: {str(e)}")
                    messages.addMessage("   → Fallback per groep...")
                    for gid in group_ids:
                        try:
                            item.sharing.groups.add(group=gid, allow_members_to_edit=True)
                            messages.addMessage(f"   → Toegevoegd aan {gid}")
                        except Exception as sub_e:
                            arcpy.AddWarning(f"   → Mislukt {gid}: {sub_e}")

                final_shared = item.shared_with
                messages.addMessage(f"   → Na delen: {final_shared.get('groups', [])}")

        # -------------------------------------------------
        # 9 Field Maps inschakelen
        # -------------------------------------------------
        messages.addMessage("Field Maps zichtbaarheid...")
        keywords = new_webmap.typeKeywords or []
        if "FieldMapsDisabled" in keywords:
            keywords = [k for k in keywords if k != "FieldMapsDisabled"]
            new_webmap.update({"typeKeywords": keywords})
            messages.addMessage("FieldMapsDisabled verwijderd")
        else:
            messages.addMessage("Al zichtbaar in Field Maps")

        # -------------------------------------------------
        # 10 Klaar
        # -------------------------------------------------
        messages.addMessage("----------------------------------")
        messages.addMessage("Project succesvol aangemaakt")
        messages.addMessage(f"Projectnummer: {projectnummer}")
        messages.addMessage(f"Map: {folder_name}")
        messages.addMessage(f"Webmap: {new_webmap.title}")
        messages.addMessage("Klaar – check groepen in AGOL!")