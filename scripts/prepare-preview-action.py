"""Repair the pinned upstream installer in an ephemeral Actions checkout.

The parent IHP repository now contains ihp-sg13cmos5l. Remove that checkout's
copy before the original installer clones and pins the standalone process repo.
Only .preview-action is modified here; the removal occurs in the CI PDK directory.
"""
from pathlib import Path

installer = Path('.preview-action/install_sg13cmos5l.sh')
text = installer.read_text()
anchor = 'git clone https://github.com/IHP-GmbH/ihp-sg13cmos5l.git "$PDK_ROOT/ihp-sg13cmos5l"'
assert text.count(anchor) == 1
repair = '''# The fresh parent checkout now includes this directory; replace it with
# the standalone process repository pinned below, as intended upstream.
[[ "$PDK_ROOT" == /home/runner/pdk ]] || exit 1
rm -rf -- "$PDK_ROOT/ihp-sg13cmos5l"
'''
parent_anchor = 'git clone --branch dev https://github.com/IHP-GmbH/IHP-Open-PDK.git "$PDK_ROOT"'
assert text.count(parent_anchor) == 1
# Retain the parent revision recorded by the baseline integrated build.
parent_pin = '\ngit -C "$PDK_ROOT" checkout 0dedf265f0cad6ef81aeb64b9ddd17eef88c0460'
text = text.replace(parent_anchor, parent_anchor + parent_pin)
installer.write_text(text.replace(anchor, repair + anchor))
