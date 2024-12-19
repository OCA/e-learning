import os
import re

import pycountry

transcript_folder = "."

languages = {
    lang.alpha_2.upper(): lang.name
    for lang in pycountry.languages
    if hasattr(lang, "alpha_2")
}


def clean_filenames(folder):
    """Remplace les espaces par des tirets du bas dans les noms de fichiers."""
    try:
        for filename in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, filename)):
                new_filename = filename.replace(" ", "_")
                if filename != new_filename:
                    os.rename(
                        os.path.join(folder, filename),
                        os.path.join(folder, new_filename),
                    )
                    # pylint: disable=W8116
                    print(f"Renamed: {filename} -> {new_filename}")
    except FileNotFoundError:
        # pylint: disable=W8116
        print(f"The folder '{folder}' does not exist.")
    except Exception as e:
        # pylint: disable=W8116
        print(f"An error occurred while cleaning filenames: {e}")


def generate_transcript_list(folder):
    """Génère une liste des fichiers transcript en format Markdown,
    en retirant les langues sans fichiers."""
    transcripts = {lang: [] for lang in languages.values()}

    try:
        for filename in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, filename)):
                for code, lang in languages.items():
                    if f"({code})" in filename:
                        transcripts[lang].append(filename)

        result = ""
        for lang, files in transcripts.items():
            if not files:
                continue

            files.sort(key=lambda x: int(re.match(r"(\d+)", x).group()))
            result += f"\n{lang}:\n"
            for file in files:
                name = (
                    re.sub(r"^\d+\s", "", file)
                    .replace("_", " ")
                    .replace(".txt", "")
                    .replace(".md", "")
                    .strip()
                )
                result += f"* [{name}](./transcript/{file})\n"

        return result

    except FileNotFoundError:
        return "The folder 'transcript' does not exist."
    except Exception as e:
        return f"An error occurred: {e}"


clean_filenames(transcript_folder)

transcript_list = generate_transcript_list(transcript_folder)
# pylint: disable=W8116
print(transcript_list)

output_path = os.path.join(transcript_folder, "../TRANSCRIPT.md")
with open(output_path, "w") as readme_file:
    readme_file.write("# Transcripts\n")
    readme_file.write(transcript_list)
    # pylint: disable=W8116
    print(f"Transcript list written to {output_path}")
