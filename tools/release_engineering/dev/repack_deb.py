# This script re-packs Drake's *.tar.gz release binaries into *.deb file(s).
#
# It currently under development and is not yet used in production.
# Known deficiencies:
#
# (*) Missing dependencies. We need to scrape the list of required packages
# from within the tgz (e.g., drake/share/drake/setup/packages-focal.txt)
# and mix that into our debian/control file. Possibly we'd want to split it
# into Depends vs Recommends vs Suggests:
# https://www.debian.org/doc/debian-policy/ch-relationships.html
#
# (*) Lots of shlibdebs spam during build. We should at least nerf the stuff
# from drake-visualizer, for starters. Possibly we shouldn't be calling
# shlibdeps at all, assuming that packages-focal.txt is authoritative.

import argparse
import email.utils
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

import lsb_release

from bazel_tools.tools.python.runfiles import runfiles


def _rlocation(relative_path):
    manifest = runfiles.Create()
    resource_path = f'drake/tools/release_engineering/dev/{relative_path}'
    resolved_path = manifest.Rlocation(resource_path)
    assert resolved_path, f'Missing {resource_path}'
    return os.path.realpath(resolved_path)


def _run(args):
    """Implements all steps for repacking tgz => deb.
    """
    # Find our runfiles.
    deb_compat = _rlocation('debian/compat')
    deb_control_in = _rlocation('debian/control.in')
    deb_copyright = _rlocation('debian/copyright')
    deb_changelog_in = _rlocation('debian/changelog.in')

    # Discern the version badging to use, get the dependencies for drake.
    codename = lsb_release.get_os_release()['CODENAME']
    with tarfile.open(args.tgz) as archive:
        version = archive.getmember('drake/share/doc/drake/VERSION.TXT')
        version_txt = archive.extractfile(version).read().decode('utf-8')
        version_mtime = version.mtime

        packages = archive.getmember(
            f'drake/share/drake/setup/packages-{codename}.txt')
        packages_txt = archive.extractfile(packages).read().decode('utf-8')

    version_tokens = version_txt.split()
    assert len(version_tokens) == 2, version_txt
    yyyymmddhhmmss, git_sha = version_tokens
    if args.version is not None:
        debian_version = args.version
    else:
        debian_version = f'0.0.{yyyymmddhhmmss}'

    # Compute the new control.  The `packages_txt` will have one package-name
    # per line; transform this to an indented and comma separated list.
    # NOTE: rstrip is required here so that the last line does *NOT* have a
    # comma (otherwise debian/rules will crash).
    depends = packages_txt.rstrip().replace('\n', ',\n         ')
    with open(deb_control_in, encoding='utf-8') as f:
        deb_control_contents = f.read().format(depends=depends)

    # Compute the new changelog.
    with open(deb_changelog_in, encoding='utf-8') as f:
        deb_changelog_contents = f.read().format(
            debian_version=debian_version,
            git_sha=git_sha,
            date=email.utils.formatdate(version_mtime),
        )

    # Use `alien` to prepare the debian packaging rules.
    cwd = f'{args.tempdir}/alien'
    os.mkdir(cwd)
    alien = [
        'fakeroot',
        '/usr/bin/alien',
        '--to-deb',
        '--single',
        f'--version={debian_version}',
        '--keep-version',
        # NOTE: the extracted permissions particularly for directories are not
        # appropriate, --fixperms results in debian/rules having `dh_fixperms`
        # which will repair the broken permissions.
        '--fixperms',
        '--verbose',
        args.tgz,
    ]
    env = dict(os.environ)
    env['EMAIL'] = 'drake-users@mit.edu'
    subprocess.check_call(alien, cwd=cwd, env=env)
    # Alien does not produce consistent directory names when extracting the
    # .tar.gz archive.  The exact pattern is not known or described in the
    # documentation, it appears to depend on both the name of the archive and
    # the --version argument.  Some examples:
    #
    # - drake-latest-focal.tar.gz => drake-latest-focal-0.0.20220513083006
    # - drake-20220512-focal.tar.gz => drake-0.0.20220512082823
    # - foo.tar.gz => foo-0.0.20220513083006
    #
    # It appears to keep the original name _until_ it finds numbers e.g.
    # 20220512.  As such, we list the directories under our alien folder and
    # assert that its length is one.  Note that regardless of the name of the
    # folder produced, the final `.deb` file will have the correct name format
    # drake-dev_{version}-1_amd64.deb.
    directories = [d for d in Path(cwd).iterdir() if d.is_dir()]
    assert len(directories) == 1, 'Unable to discover alien output directory.'
    package_dir = str(directories[0])

    # Install into /opt/drake, not /drake.
    os.mkdir(f'{package_dir}/opt')
    os.rename(f'{package_dir}/drake',
              f'{package_dir}/opt/drake')

    # Overwrite some metadata.
    shutil.copy(deb_compat, f'{package_dir}/debian/')
    with open(f'{package_dir}/debian/control', 'w', encoding='utf-8') as f:
        f.write(deb_control_contents)
    shutil.copy(deb_copyright, f'{package_dir}/debian/')
    with open(f'{package_dir}/debian/changelog', 'w', encoding='utf-8') as f:
        f.write(deb_changelog_contents)

    # Create the deb.
    subprocess.check_call(['fakeroot', 'debian/rules', 'binary'],
                          cwd=package_dir)
    shutil.move(f'{cwd}/drake-dev_{debian_version}-1_amd64.deb',
                f'{args.output_dir}/')


def main():
    parser = argparse.ArgumentParser(
        description='Re-package Drake into Debian files.')
    parser.add_argument(
        '--tgz', type=str, required=True,
        help='the foo.tar.gz filename to be re-packaged')
    parser.add_argument(
        '--output-dir', metavar='DIR', default=os.path.realpath('.'),
        help='directory to place *.deb output (default: .)')
    parser.add_argument(
        '--version', type=str, required=False, default=None,
        help=(
            'version number to package (e.g., "1.3.0"), if not specified the '
            'date timestamp YYYYMMDD found in the foo.tar.gz file '
            'drake/share/doc/drake/VERSION.TXT will be used'))
    args = parser.parse_args()
    args.tgz = os.path.realpath(args.tgz)

    with tempfile.TemporaryDirectory(prefix='drake-repack-') as tempdir:
        args.tempdir = tempdir
        _run(args)


if __name__ == '__main__':
    main()
