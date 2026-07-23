from importer.html_importer import HtmlImporter

def test_missing_export_elements(tmp_path):
    assert set(HtmlImporter(tmp_path).validate()) == {"index.html", "lista.html", "plany"}


def test_group_marker_is_detected_anywhere_and_hyphen_is_removed():
    data = HtmlImporter._cell_data("Język angielski -1/2 3TA")
    assert data["group_name"] == "1/2"
    assert data["class_name"] == "3TA"
    assert data["subject"] == "Język angielski"


def test_group_marker_directly_after_class_is_detected():
    data = HtmlImporter._cell_data("4T_C-3/3 pr.apl.deskt")
    assert data["group_name"] == "3/3"
    assert data["class_name"] == "4T_C"
    assert data["subject"] == "pr.apl.deskt"


def test_lesson_without_group_remains_whole_class_lesson():
    data = HtmlImporter._cell_data("2TB matematyka")
    assert data["group_name"] is None
    assert data["class_name"] == "2TB"
    assert data["subject"] == "matematyka"


def test_roman_group_name_is_detected():
    data = HtmlImporter._cell_data("Język łaciński -II/1 3TA")
    assert data["group_name"] == "II/1"
    assert data["class_name"] == "3TA"
    assert data["subject"] == "Język łaciński"


def test_any_group_name_after_hyphen_is_detected():
    data = HtmlImporter._cell_data("4T_C-G1 pracownia")
    assert data["group_name"] == "G1"
    assert data["class_name"] == "4T_C"
    assert data["subject"] == "pracownia"


def test_numeric_room_is_removed_from_subject():
    data = HtmlImporter._cell_data("2TA -1/2 pneum 16A")
    assert data["room"] == "16A"
    assert data["subject"] == "pneum"


def test_w_room_is_removed_from_subject():
    data = HtmlImporter._cell_data("4T_A -1/3 obsł.urz.mec W10")
    assert data["room"] == "W10"
    assert data["subject"] == "obsł.urz.mec"


def test_sala_room_with_space_is_removed_from_subject():
    data = HtmlImporter._cell_data("3LA -1/2 wf SALA GIM2")
    assert data["room"] == "SALA GIM2"
    assert data["subject"] == "wf"


def test_sala_room_with_underscore_is_removed_from_subject():
    data = HtmlImporter._cell_data("3TC -1/2 wf SALA_GIM1")
    assert data["room"] == "SALA_GIM1"
    assert data["subject"] == "wf"


def test_ckz_room_is_removed_from_subject():
    data = HtmlImporter._cell_data("4T_C -1/2 lotn-warsztaty CKZ_AK")
    assert data["room"] == "CKZ_AK"
    assert data["subject"] == "lotn-warsztaty"


def test_lowercase_subject_starting_with_w_is_not_room():
    data = HtmlImporter._cell_data("2TA witryny")
    assert data["room"] is None
    assert data["subject"] == "witryny"


def test_room_at_symbol():
    data = HtmlImporter._cell_data("3LA -1/2 wf @")
    assert data["room"] == "@"
    assert data["subject"] == "wf"
    assert data["participants"] == (("3LA", "1/2"),)


def test_combined_groups_from_two_classes():
    data = HtmlImporter._cell_data("3TA -3/3, 3TB -2/2 j.hiszpański 8")
    assert data["participants"] == (("3TA", "3/3"), ("3TB", "2/2"))
    assert data["class_name"] == "3TA"
    assert data["group_name"] == "3/3"
    assert data["subject"] == "j.hiszpański"
    assert data["room"] == "8"
