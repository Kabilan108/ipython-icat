# ipython-icat

[![PyPI version](https://img.shields.io/pypi/v/ipython-icat.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ipython-icat/)

## Installation

You can install `ipython-icat` using pip:

```bash
pip install ipython-icat
```

## Requirements

- Python 3.10+
- IPython
- matplotlib
- Pillow (PIL)
- terminal emulator with support for kitty graphics protocol (KGP) e.g., kitty, ghostty

## Usage

### Loading the Extension

In your IPython session, load the extension:

```python
%load_ext icat
```

For startup files, Neovim terminals, or other launchers that should enable the
backend immediately after loading the extension, set:

```bash
IPYTHON_ICAT_AUTO=1
```

### Displaying Matplotlib Plots

To enable `icat` integration for both matplotlib plots and automatic PIL image rendering:

```python
%icat
```

After running this command:
- Matplotlib plots will be displayed directly in your kitty-compatible terminal.
- Evaluating a `PIL.Image.Image` value (e.g. typing `img` at the prompt) will automatically render it.

You can also run:
- `%icat status` to see whether integration is enabled
- `%icat off` to disable auto-rendering and restore the previous matplotlib backend (best-effort)

### Use as a Default Backend

To set the kitty backend for matplotlib as the default, add the following lines to your IPython configuration file:

1. `c.InteractiveShellApp.extensions = ['icat']`
2. `c.InteractiveShellApp.exec_lines = ['%icat on']`

#### Automatic Setup

You can quickly set up IPython to use the icat extension using the setup command:

```bash
python -m icat setup
```

This command will:
1. Create an IPython profile if it doesn't exist (or use an existing one)
2. Configure the profile to load the icat extension automatically
3. Set matplotlib to use the icat backend by default

Additional options:
- `--profile NAME` - Use a specific profile instead of the default
- `--ipython-path PATH` - Specify a custom path to the .ipython directory

Example with custom profile:
```bash
python -m icat setup --profile myprofile
```

### Displaying Images

To display an image file, a PIL Image object, or a Python expression that evaluates to a PIL Image:

```python
%icat path/to/your/image.jpg
```

or

```python
from PIL import Image
img = Image.open('path/to/your/image.jpg')
%icat img
```

Expressions work too:

```python
%icat ds[0].image
```

You can also resize the image when displaying:

```python
%icat path/to/your/image.jpg -W 300 -H 200
```

### Using Ghostty

If you'd like to use this plugin with Ghostty, make sure to install the [static kitten binary](https://github.com/kovidgoyal/kitty/releases) which will allow you to run `kitten icat`.

### Using Full-Screen Terminal Apps

`ipython-icat` can render through full-screen terminal programs, such as Neovim
terminal buffers, by asking `kitten icat` to emit Kitty unicode placeholders.
Enable that mode with:

```bash
IPYTHON_ICAT_PLACEHOLDER=1
```

The placeholder path is configured with environment variables:

- `IPYTHON_ICAT_CELL_PIXELS=WIDTHxHEIGHT` supplies the terminal cell size in
  pixels. This lets `kitten icat` compute the window size when IPython is
  running inside an embedded terminal.
- `IPYTHON_ICAT_WINDOW_SIZE=COLS,ROWS,WIDTH_PX,HEIGHT_PX` overrides the
  computed window size completely.
- `IPYTHON_ICAT_TRANSFER_MODE=stream|file|memory|detect` selects the Kitty
  graphics transfer mode. The default is `stream`, which works reliably through
  Neovim and Ghostty.
- `IPYTHON_ICAT_PASSTHROUGH=none|tmux|detect` controls whether `kitten icat`
  wraps graphics commands for tmux. The default is `none`; use this when a host
  program relays the graphics request itself.

[`pyrepl.nvim`](https://github.com/Kabilan108/pyrepl.nvim) sets these variables
automatically when starting IPython and relays Kitty graphics requests from the
embedded terminal to the host terminal.

## Features

- Display matplotlib plots directly in kitty terminal
- Show PIL Image objects or image files
- Resize images on display
- Seamless integration with IPython workflow
- Kitty unicode-placeholder support for embedded terminal workflows

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [matplotlib-backend-kitty](https://github.com/jktr/matplotlib-backend-kitty) for the original implementation
- [matplotlib](https://github.com/matplotlib/matplotlib) and [Pillow](https://python-pillow.org/) for their excellent libraries
- [kitty terminal](https://github.com/kovidgoyal/kitty) for developing the graphics protocol

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
