# Lesen der aktualisierten Kategorien-Datei mit Bindestrichen zur Kennzeichnung der Hierarchie
file_path = 'categories/extracted_categories.txt'

with open(file_path, 'r', encoding='utf-8') as file:
    category_lines = file.readlines()

# Verarbeitung der Kategorien in das gewünschte Format
main_categories = []
subcategories = {}

for line in category_lines:
    # Entfernen von Zeilenumbrüchen und führenden Leerzeichen
    line = line.strip()

    # Trennen der Daten und Entfernen von überflüssigen Leerzeichen
    if ',' in line:
        data_val, text = line.split(',', 1)
        data_val, text = data_val.strip(), text.strip()

        # Überprüfen des Einrückungsniveaus
        if line.startswith("-"):  # Hauptkategorie
            main_categories.append({"title": text, "callback_data": f"category_main_{data_val}"})
            subcategories[data_val] = []
            current_main_category = data_val
        elif line.startswith("--"):  # Unterkategorie
            subcategories[current_main_category].append({"title": text, "callback_data": f"category_sub_{data_val}"})


            
print(subcategories)