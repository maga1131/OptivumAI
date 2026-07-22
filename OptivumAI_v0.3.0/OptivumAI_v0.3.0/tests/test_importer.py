from importer.html_importer import HtmlImporter

def test_missing_export_elements(tmp_path):
    assert set(HtmlImporter(tmp_path).validate()) == {"index.html", "lista.html", "plany"}
