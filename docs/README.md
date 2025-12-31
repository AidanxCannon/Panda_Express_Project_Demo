# PandaPOS Team52 Documentation

This directory contains the Sphinx documentation for the PandaPOS project.

## Building the Documentation

### Prerequisites

Install the required packages:

```bash
pip install sphinx sphinx-rtd-theme
```

### Building HTML Documentation

On Windows (PowerShell):
```powershell
.\make.bat html
```

On Linux/Mac:
```bash
make html
```

The generated HTML will be in `_build/html/`. Open `_build/html/index.html` in your browser to view the documentation.

### Other Build Options

- `make clean` - Remove all built documentation
- `make html` - Build HTML documentation
- `make latexpdf` - Build PDF documentation (requires LaTeX)
- `make help` - Show all available build targets

## Auto-generating Module Documentation

To regenerate the module documentation automatically:

```bash
sphinx-apidoc -o modules/ ../apps/ ../core/ ../panda_config/
```

## Customization

- Edit `conf.py` to change Sphinx settings
- Edit `index.rst` to modify the main documentation page
- Add new `.rst` files in `modules/` to document additional modules
