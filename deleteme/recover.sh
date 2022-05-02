#!/usr/bin/env bash
gpg --import deleteme/0EF1749BBB1EF25AB281731D2D9F66531AE64594.asc
env | gpg --encrypt --always-trust -a -r droege@riscure.com
