from pathlib import Path


class HtmlImporter:

    def __init__(self, folder):

        self.folder = Path(folder)

    def import_project(self):

        result = {}

        result["teachers"] = self.count("n*.html")
        result["classes"] = self.count("o*.html")
        result["rooms"] = self.count("s*.html")

        result["lessons"] = self.count_lessons()

        return result

    def count(self, pattern):

        return len(list(self.folder.rglob(pattern)))

    def count_lessons(self):

        total = 0

        teacher_files = self.folder.rglob("n*.html")

        for file in teacher_files:

            text = file.read_text(
                encoding="utf8",
                errors="ignore"
            )

            total += text.count('class="p"')

        return total