# Documentation

This directory contains documentation and PDF generation scripts for the lx-euclid project.

## Files

- `EEPROM_Structure.md` - Detailed EEPROM register documentation
- `generate_pdf.sh` - Ubuntu/Linux script to generate PDF documentation

## Prerequisites

### Required Software (Ubuntu/Linux)

1. **Pandoc** - Document converter
2. **LaTeX distribution** - For PDF generation (pdflatex)

### Installation Instructions

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

## Usage

1. Open a terminal
2. Navigate to the `docs` directory
3. Make the script executable and run it:

   ```bash
   chmod +x generate_pdf.sh
   ./generate_pdf.sh
   ```

## Output

The script will generate `EEPROM_Structure.pdf` in the same directory.

## Troubleshooting

### Common Issues

1. **"pandoc is not installed"**
   - Install pandoc following the instructions above
   - Make sure it's in your PATH

2. **"pdflatex is not installed"**
   - Install texlive packages following the instructions above
   - Make sure pdflatex is in your PATH

3. **"EEPROM_Structure.md not found"**
   - Make sure you're running the script from the docs directory
   - The markdown file should be in the same folder as the script

4. **PDF generation fails with LaTeX errors**
   - Try updating your LaTeX distribution
   - Make sure all required texlive packages are installed
