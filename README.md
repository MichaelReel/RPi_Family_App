# RPi Full Screen Portal Application

Just want to have a full screen app for a RPi + Touch Screen.

Current version is a Clock and a weekly Weather panel.

## Install from repo

Clone this repository and cd into it:

```sh
git clone https://github.com/MichaelReel/RPi_Family_App.git
cd RPi_Family_App
```

### Setup on Linux (non-Raspbian)

Create a python environment and install uv

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install uv
```

> You will need to use `source .venv/bin/activate` to activate the python environment each time you open this folder in a new shell, or if you source another python environment.
> If you ever see "command not found" it can mean the environment hasn't been activated.

The App will need dependencies installed. `uv sync` will handle most dependencies, but we also need PyQT6 installed which has been left out of the pyproject.toml.
On a normal linux environment this should be as simple as:

```
uv sync
uv pip install pyqt6
```

To run the app, `source .venv/bin/activate` if necessary, then:

```
uv run main.py
```

### Setup on Raspbian

On Raspbian the depencies are a little more involved. Install these system packages and set the pipx path:

```
sudo apt update
sudo apt install -y python3-pyqt6 pipx
pipx ensurepath
```

Open an new terminal (or `source ~/.bashrc`) to ensure that ~/.local/bin is on the path. Then install uv:

```
pipx install uv
```

Create a virtual env, activate it and install the rest of the dependencies:

```
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
uv pip install -r pyproject.toml
```

Cross your fingers and try to run the script:

```
python3 maii.py
```


