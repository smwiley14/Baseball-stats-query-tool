#!/bin/bash

# Script to process retrosheet box score files using cwbox
# This processes all .EBN and .EBA files in the box_scores directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

SRC_DIR="data/box_scores"
OUTPUT_DIR="data/processed/box_scores"
mkdir -p "$OUTPUT_DIR"

echo "Processing retrosheet box score files..."

# Check if cwbox is available
if ! command -v cwbox &> /dev/null; then
    echo "Warning: cwbox not found. Skipping box score processing."
    echo "Note: cwbox may not be available in all chadwick distributions."
    exit 0
fi

# Process each decade directory
for decade_dir in "$SRC_DIR"/*box; do
    if [ -d "$decade_dir" ]; then
        decade=$(basename "$decade_dir" | sed 's/box$//')
        echo "Processing decade: $decade"
        
        # Extract year from decade (e.g., 1890sbox -> 1890)
        year_start="${decade:0:3}0"
        
        # Process each year in the decade
        for year in $(seq $year_start $((year_start + 9))); do
            # Check if year files exist
            ebn_files=$(find "$decade_dir" -name "${year}.EBN" | head -1)
            eba_files=$(find "$decade_dir" -name "${year}.EBA" | head -1)
            
            if [ -n "$ebn_files" ] || [ -n "$eba_files" ]; then
                echo "  Processing year: $year"
                
                output_file="$OUTPUT_DIR/box_scores_${year}.csv"
                
                if [ -f "$output_file" ]; then
                    echo "    Skipping $year (output already exists)"
                    continue
                fi
                
                cd "$decade_dir"
                
                # Create team file symlink if TEAM file exists for this year
                team_file=$(find . -iname "TEAM${year}" -o -iname "team${year}" 2>/dev/null | head -1)
                if [ -n "$team_file" ] && [ ! -f "team" ]; then
                    ln -s "$team_file" "team" 2>/dev/null || cp "$team_file" "team" 2>/dev/null
                fi
                
                # Run cwbox and filter out version/help messages
                # cwbox outputs box scores in a specific format - keep data lines
                # Box scores may not always start with quotes, so we'll filter differently
                cwbox -y "$year" "${year}".EB* 2>&1 | \
                    grep -v "^Chadwick" | \
                    grep -v "^  Type" | \
                    grep -v "^Copyright" | \
                    grep -v "^This is free" | \
                    grep -v "^Dr T L" | \
                    grep -v "^\[Processing" | \
                    grep -v "^Can't find" | \
                    grep -v "^$" > "$PROJECT_ROOT/$output_file" || true
                
                # Clean up team symlink
                if [ -L "team" ]; then
                    rm -f "team"
                fi
                
                cd "$PROJECT_ROOT"
                
                if [ -s "$output_file" ]; then
                    echo "    Created: $output_file"
                else
                    echo "    Warning: $output_file is empty or failed"
                    rm -f "$output_file"
                fi
            fi
        done
    fi
done

echo "Box score processing complete!"

