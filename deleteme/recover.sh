#!/usr/bin/env bash
gpg --import deleteme/Stefan_Droege.asc
env | gpg --encrypt --always-trust -a -r stefan@sdroege.de
