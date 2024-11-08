#!/bin/bash

DEFAULT_MODULE="${1:-elearning_data}"

get_fragment_type() {
    local commit_type="$1"
    case "$commit_type" in
        FIX|BUG|HOTFIX) echo "bugfix" ;;
        IMP|UPT) echo "feature" ;;
        CI) echo "misc" ;;
        *) echo "misc" ;;
    esac
}

module_exists() {
    local module="$1"
    [[ -d "$module" ]]
}

commit_in_history() {
    local module="$1"
    local commit_hash="$2"
    local history_file="${module}/readme/HISTORY.md"
    [[ -f "$history_file" ]] && grep -q "$commit_hash" "$history_file"
}

fragment_exists() {
    local fragment_file="$1"
    [[ -f "$fragment_file" ]]
}

unreleased_commits=$(git log --pretty=format:"%H %s" HEAD)

while IFS= read -r line; do
    commit_hash=$(echo "$line" | awk '{print $1}')
    commit_msg=$(echo "$line" | cut -d' ' -f2-)

    if [[ "$commit_msg" =~ \[([A-Z]+)\](\ ([^:]+):)?\ (.*) ]]; then
        commit_type=${BASH_REMATCH[1]}
        module_name=${BASH_REMATCH[3]:-$DEFAULT_MODULE}
        message=${BASH_REMATCH[4]}
    else
        echo "Invalid commit format for: $commit_msg"
        continue
    fi

    if ! module_exists "$module_name"; then
        # echo "Module '$module_name' not found. Using default module '$DEFAULT_MODULE'."
        module_name="$DEFAULT_MODULE"
    fi

    if commit_in_history "$module_name" "$commit_hash"; then
        # echo "Commit $commit_hash already present in $module_name/readme/HISTORY.md. No fragment created."
        continue
    fi

    fragment_type=$(get_fragment_type "$commit_type")
    fragment_dir="${module_name}/readme/newsfragments"
    fragment_filename="$fragment_dir/${commit_hash}.${fragment_type}.md"

    if fragment_exists "$fragment_filename"; then
        # echo "Fragment for commit $commit_hash already exists at $fragment_filename. No fragment created."
        continue
    fi

    mkdir -p "$fragment_dir"
    echo "$message" > "$fragment_filename"
    echo "Fragment created: $fragment_filename"
done <<< "$unreleased_commits"
