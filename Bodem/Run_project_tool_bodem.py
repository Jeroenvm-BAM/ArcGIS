# -*- coding: utf-8 -*-
import arcpy
import sys
import warnings

# Alleen ResourceWarnings onderdrukken (deze komen van tempfile cleanup in arcgis API)
warnings.filterwarnings("ignore", category=ResourceWarning)

# Pad naar de Python Toolbox (.pyt) file
pyt_path = r"C:\GIS\Nieuw_Project_Bodem.pyt"

# Importeer de toolbox
arcpy.ImportToolbox(pyt_path)

def main():
    if len(sys.argv) != 3:
        print("Gebruik: python run_project_tool.py <projectnummer> <projectnaam>")
        sys.exit(1)
    
    projectnummer = sys.argv[1].strip()
    projectnaam = sys.argv[2].strip()
    
    print(f"Uitvoeren van tool met projectnummer: {projectnummer} en projectnaam: {projectnaam}")
    
    # Roep de tool aan
    arcpy.MaakNieuwProject_fieldmaps_project(projectnummer, projectnaam)
    
    print("Tool succesvol uitgevoerd.")

if __name__ == "__main__":
    main()