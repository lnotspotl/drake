---
title: Installation via Pip
---

# Pip Packages

Drake publishes pre-compiled binaries as
[PyPI wheel packages](https://pypi.org/project/drake/).  Refer to
[Supported Configurations](/installation.html#supported-configurations)
for additional compatibility details.  Drake wheels require a `pip`
version of `pip >= 20.3`.

To learn about other installation methods, refer to
[Installation and Quickstart](/installation.html).

If you experience any problems or questions with Drake, please
[ask for help on Stack Overflow](/getting_help.html).

Drake binary releases incorporate a pre-compiled version of
[SNOPT](https://ccom.ucsd.edu/~optimizers/solvers/snopt/) as part of the
[Mathematical Program toolbox](https://drake.mit.edu/doxygen_cxx/group__solvers.html).
Thanks to Philip E. Gill and Elizabeth Wong for their kind support.

Drake's pip packages do not support the Gurobi solver. To use
Gurobi, you will need to [build Drake from source](/from_source.html).

## Stable Releases

<div class="warning" markdown="1">
Drake's pip wheels are only published for CPython 3.6 through CPython 3.9
running on Linux.  In the future, we intend to publish macOS wheel builds.
</div>

<div class="warning" markdown="1">
Support for CPython 3.6 and CPython 3.7 will end on 2022-04-01.
</div>

<div class="warning" markdown="1">
Drake does not support the Python environment supplied by Anaconda. Before
installing or using Drake, please `conda deactivate` (repeatedly, until even
the conda base environment has been deactivated) such that none of the paths
reported `which -a python python3 pip pip3` refer to conda.
</div>

<div class="warning" markdown="1">
Drake's support for pip has a few known issues (see
[issue #15954](https://github.com/RobotLocomotion/drake/issues/15954)).
Please [let us know](/getting_help.html) if you
experience any additional problems. To fall back to other installation methods
in the meantime, refer to [Installation and Quickstart](/installation.html)
for more choices.
</div>

We recommend installing drake into a
[virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)
directory.  In the example below, we will name that directory ``env``, but you
can choose any name.

Create a virtual environment and install Drake:

```bash
python3 -m venv env
env/bin/pip install --upgrade pip
env/bin/pip install drake
```

Drake requires certain basic runtime libraries from the host linux distribution.

For Ubuntu 20.04, install these additional libraries:

```bash
sudo apt-get install --no-install-recommends \
  libpython3.8 libx11-6 libsm6 libxt6 libglib2.0-0
```

Activate the virtual environment:

```bash
source env/bin/activate
````

Refer to [Quickstart](/installation.html#quickstart) for next steps.
