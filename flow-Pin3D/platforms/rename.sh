#!/bin/bash

target_directory="nangate45_3D/lef_upper"
cd "$target_directory"

for file in *.lef; do
    if [[ -f $file ]]; then
        base_name="${file%.lef}"
        new_name="${base_name}.upper.lef"
        mv "$file" "$new_name"
        echo "Renamed $file to $new_name"
    fi
done