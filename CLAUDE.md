# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ipython-icat is a Python package that provides IPython magic commands for displaying images and matplotlib plots directly in terminal emulators that support the kitty graphics protocol (KGP), such as kitty and ghostty.

## Development Commands

### Nix Devshell

Run Python commands inside the `flake.nix` devshell (it sets `LD_LIBRARY_PATH` so native deps like `matplotlib` import correctly):

```bash
# Default (py38)
nix develop

# Or select a specific shell
nix develop .#py312
```

### Environment Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"
```

### Testing

To manually test the functionality:

```bash
# Start IPython
ipython

# Within IPython, load the extension
%load_ext icat

# Enable the kitty backend for matplotlib
%plt_icat

# Display an image
%icat path/to/image.jpg

# Display with specific dimensions
%icat path/to/image.jpg -w 300 -h 200
```

### Building & Publishing

Handled by CI (GitHub Actions).

## Architecture

The project is fairly simple with a single main module:

1. **icat/\__init__.py**: Contains all the functionality including:
   - `ICatMagics` class: Defines IPython magic commands (%icat and %plt_icat)
   - Matplotlib backend implementation based on matplotlib-backend-kitty
   - Functions to display PIL Image objects through the kitty terminal protocol

The implementation uses the kitty terminal graphics protocol to render images and plots directly in compatible terminal emulators. It requires the "kitten" executable to be available in the system path.

Key features:
- Display matplotlib plots using a custom backend
- Show image files or PIL Image objects directly in the terminal
- Resize images on display
