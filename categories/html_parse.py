from bs4 import BeautifulSoup

# Opening and reading the uploaded HTML file
file_path = 'categories/kleinanzeigen_kategorien.html'

with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parsing the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extracting data-val and text content for each <a> tag with both class and data-val attributes
extracted_elements = []
for a_tag in soup.find_all('a', attrs={"class": True, "data-val": True}):
    data_val = a_tag.get("data-val")
    text_content = a_tag.get_text(strip=True)
    extracted_elements.append((data_val, text_content))

# Function to save the extracted elements to a file

def save_extracted_elements_to_file(extracted_elements, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for element in extracted_elements:
            # Entfernen von zusätzlichen Leerzeichen und Zeilenumbrüchen
            cleaned_text = ' '.join(element[1].split())
            file.write(f'{element[0]}, {cleaned_text}\n')
    return file_path


# Saving the extracted elements to a file
saved_file_path = save_extracted_elements_to_file(extracted_elements, 'categories/extracted_categories.txt')




