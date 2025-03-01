#!/bin/bash
#
# Install development prerequisites for source distributions of Drake on
# Ubuntu 20.04 (Focal).
#
# The development and runtime prerequisites for binary distributions should be
# installed before running this script.

set -euo pipefail

with_doc_only=0
# TODO(betsymcphail): Remove this deprecated option on or after 2022-08-01
with_kcov=0
with_maintainer_only=0
with_clang=1
with_test_only=1
with_update=1
with_asking=1

# TODO(jwnimmer-tri) Eventually we should default to with_clang=0.

while [ "${1:-}" != "" ]; do
  case "$1" in
    # Install prerequisites that are only needed to build documentation,
    # i.e., those prerequisites that are dependencies of bazel run //doc:build.
    --with-doc-only)
      with_doc_only=1
      ;;
    # TODO(betsymcphail): Remove this deprecated option on or after 2022-08-01
    --with-kcov)
      with_kcov=1
      ;;
    # Install prerequisites that are only needed for --config clang, i.e.,
    # opts-in to the ability to compile Drake's C++ code using Clang.
    --with-clang)
      with_clang=1
      ;;
    # Do NOT install prerequisites that are only needed for --config clang,
    # i.e., opts-out of the ability to compile Drake's C++ code using Clang.
    --without-clang)
      with_clang=0
      ;;
    # Install prerequisites that are only needed to run select maintainer
    # scripts. Most developers will not need to install these dependencies.
    --with-maintainer-only)
      with_maintainer_only=1
      ;;
    # Do NOT install prerequisites that are only needed to build and/or run
    # unit tests, i.e., those prerequisites that are not dependencies of
    # bazel { build, run } //:install.
    --without-test-only)
      with_test_only=0
      ;;
    # Do NOT call apt-get update during execution of this script.
    --without-update)
      with_update=0
      ;;
    # Pass -y along to apt-get.
    -y)
      with_asking=0
      ;;
    *)
      echo 'Invalid command line argument' >&2
      exit 3
  esac
  shift
done

if [[ "${EUID}" -ne 0 ]]; then
  echo 'ERROR: This script must be run as root' >&2
  exit 1
fi

if [[ "${with_asking}" -eq 0 ]]; then
  maybe_yes='-y'
else
  maybe_yes=''
fi

if [[ "${with_update}" -eq 1 && "${binary_distribution_called_update:-0}" -ne 1 ]]; then
  apt-get update || (sleep 30; apt-get update)
fi

apt-get install ${maybe_yes} --no-install-recommends $(cat <<EOF
ca-certificates
wget
EOF
)

codename=$(lsb_release -sc)

packages=$(cat "${BASH_SOURCE%/*}/packages-${codename}.txt")
apt-get install ${maybe_yes} --no-install-recommends ${packages}


# TODO(svenevs): Ideally we would have `packages-${codename}-satisfy.txt`,
# an example workflow is in #16233 but xargs needs work (see #16280).
apt-get satisfy  ${maybe_yes} --no-install-recommends \
  'libcurl4-gnutls-dev | libcurl4-dev'

# Ensure that we have available a locale that supports UTF-8 for generating a
# C++ header containing Python API documentation during the build.
apt-get install ${maybe_yes} --no-install-recommends locales
locale-gen en_US.UTF-8

if [[ "${codename}" == 'focal' ]]; then
  # We need a working /usr/bin/python (of any version).
  # On Focal we have to ask for it.
  if [[ ! -e /usr/bin/python ]]; then
    apt-get install ${maybe_yes} --no-install-recommends python-is-python3
  else
    echo "/usr/bin/python is already installed"
  fi
fi

if [[ "${with_doc_only}" -eq 1 ]]; then
  packages=$(cat "${BASH_SOURCE%/*}/packages-${codename}-doc-only.txt")
  apt-get install ${maybe_yes} --no-install-recommends ${packages}
fi

if [[ "${with_clang}" -eq 1 ]]; then
  packages=$(cat "${BASH_SOURCE%/*}/packages-${codename}-clang.txt")
  apt-get install ${maybe_yes} --no-install-recommends ${packages}
fi

if [[ "${with_test_only}" -eq 1 ]]; then
  packages=$(cat "${BASH_SOURCE%/*}/packages-${codename}-test-only.txt")
  # Suppress Python 3.8 warnings when installing python3-pandas on Focal.
  PYTHONWARNINGS=ignore::SyntaxWarning \
    apt-get install ${maybe_yes} --no-install-recommends ${packages}
fi

if [[ "${with_maintainer_only}" -eq 1 ]]; then
  packages=$(cat "${BASH_SOURCE%/*}/packages-${codename}-maintainer-only.txt")
  apt-get install ${maybe_yes} --no-install-recommends ${packages}
fi

dpkg_install_from_wget() {
  package="$1"
  version="$2"
  url="$3"
  checksum="$4"

  # Skip the install if we're already at the exact version.
  installed=$(dpkg-query --showformat='${Version}\n' --show "${package}" 2>/dev/null || true)
  if [[ "${installed}" == "${version}" ]]; then
    echo "${package} is already at the desired version ${version}"
    return
  fi

  # If installing our desired version would be a downgrade, ask the user first.
  if dpkg --compare-versions "${installed}" gt "${version}"; then
    echo "This system has ${package} version ${installed} installed."
    echo "Drake suggests downgrading to version ${version}, our supported version."
    read -r -p 'Do you want to downgrade? [Y/n] ' reply
    if [[ ! "${reply}" =~ ^([yY][eE][sS]|[yY])*$ ]]; then
      echo "Skipping ${package} ${version} installation."
      return
    fi
  fi

  # Download and verify.
  tmpdeb="/tmp/${package}_${version}-amd64.deb"
  wget -O "${tmpdeb}" "${url}"
  if echo "${checksum} ${tmpdeb}" | sha256sum -c -; then
    echo  # Blank line between checkout output and dpkg output.
  else
    echo "ERROR: The ${package} deb does NOT have the expected SHA256. Not installing." >&2
    exit 2
  fi

  # Install.
  dpkg -i "${tmpdeb}"
  rm "${tmpdeb}"
}

# Install bazel package dependencies (these may duplicate dependencies of
# drake).
apt-get install ${maybe_yes} --no-install-recommends $(cat <<EOF
g++
unzip
zlib1g-dev
EOF
)

dpkg_install_from_wget \
  bazel 5.1.0 \
  https://releases.bazel.build/5.1.0/release/bazel_5.1.0-linux-x86_64.deb \
  3d54055f764cfb61b5416f0a45d2d3df19c30d301d4da81565595cbe2e36a220

# TODO(betsymcphail): Remove this deprecated option on or after 2022-08-01
if [[ "${with_kcov}" -eq 1 ]]; then
  echo 'WARNING: The --with-kcov option is deprecated and should no longer be used.' >&2
fi
