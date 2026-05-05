#!/bin/bash

# Local PDF generation script for EEPROM Structure documentation
# Ubuntu/Linux only version

set -e

echo "🔄 Local PDF Generation Script"
echo "=============================="

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc is not installed"
    echo "📋 Installation instructions:"
    echo "   sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra"
    exit 1
fi

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "❌ pdflatex is not installed"
    echo "📋 Installation instructions:"
    echo "   sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-latex-extra"
    exit 1
fi

# Check if the markdown file exists
if [ ! -f "EEPROM_Structure.md" ]; then
    echo "❌ EEPROM_Structure.md not found in current directory"
    echo "📂 Make sure you're running this script from the docs directory"
    exit 1
fi

echo "✅ Dependencies check passed"
echo "📄 Converting EEPROM_Structure.md to PDF..."


# Run pandoc conversion
pandoc EEPROM_Structure.md \
  -o EEPROM_Structure.pdf \
  --pdf-engine=pdflatex \
  --variable geometry:"top=0.4in,bottom=0.4in,left=0.4in,right=0.4in" \
  --variable fontsize=7pt \
  --variable documentclass=article \
  --variable classoption="a4paper" \
  --variable tables=true \
  --variable colorlinks=true \
  --wrap=preserve


if [ -f "EEPROM_Structure.pdf" ]; then
    echo "✅ PDF generated successfully!"
    echo "📁 Output: EEPROM_Structure.pdf"
    ls -la EEPROM_Structure.pdf

    # Try to open the PDF using xdg-open (Linux)
    if command -v xdg-open &> /dev/null; then
        xdg-open EEPROM_Structure.pdf
    else
        echo "🔍 Open EEPROM_Structure.pdf manually to view the result"
    fi
else
    echo "❌ PDF generation failed"
    exit 1
fi