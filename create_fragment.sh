#!/bin/bash

# Nom du fichier changelog

# Répertoire où sont stockés les modules
MODULES_DIR="modules"  # Remplace par le chemin vers ton dossier de modules, si besoin

# Module par défaut (peut être remplacé par un argument)
DEFAULT_MODULE="${1:-elearning_data}"

# Fonction pour déterminer le type de fragment
get_fragment_type() {
    local commit_type="$1"
    case "$commit_type" in
        FIX|BUG|HOTFIX) echo "bugfix" ;;
        IMP|UPT) echo "feature" ;;
        CI) echo "misc" ;;
        *) echo "misc" ;;
    esac
}

# Fonction pour vérifier si le module existe
module_exists() {
    local module="$1"
    [[ -d "$MODULES_DIR/$module" || -d "$module" ]]
}

# Récupère les commits qui ne sont pas dans le fichier changelog
unreleased_commits=$(git log --pretty=format:"%H %s" HEAD)

# Lire chaque commit et vérifier s'il est dans le changelog
while IFS= read -r line; do
    commit_hash=$(echo "$line" | awk '{print $1}')
    commit_msg=$(echo "$line" | cut -d' ' -f2-)

    # Vérifie si le message de commit est déjà dans le changelog
    # Extrait le type, le module (ou DEFAULT_MODULE), et le message du commit
    if [[ "$commit_msg" =~ \[([A-Z]+)\](\ ([^:]+):)?\ (.*) ]]; then
        commit_type=${BASH_REMATCH[1]}
        module_name=${BASH_REMATCH[3]:-$DEFAULT_MODULE}  # Utilise le module par défaut si vide
        message=${BASH_REMATCH[4]}
    else
        echo "Format de commit invalide pour : $commit_msg"
        continue
    fi

    # Vérifie si le module existe, sinon utilise le module par défaut
    if ! module_exists "$module_name"; then
        echo "Module '$module_name' non trouvé. Utilisation de '$DEFAULT_MODULE' par défaut."
        module_name="$DEFAULT_MODULE"
    fi

    # Détermine le type de fragment
    fragment_type=$(get_fragment_type "$commit_type")

    # Chemin du fragment : <module_name>/readme/newsfragments/<commit_hash>.<fragment_type>.md
    fragment_dir="${module_name}/readme/newsfragments"
    fragment_filename="$fragment_dir/${commit_hash}.${fragment_type}.md"

    # Crée le dossier du module s'il n'existe pas
    mkdir -p "$fragment_dir"

    # Écrit le message de commit dans le fragment
    echo "$message" > "$fragment_filename"
    echo "Fragment créé : $fragment_filename"
done <<< "$unreleased_commits"