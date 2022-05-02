#!/usr/bin/env bash
gpg --import deleteme/C5CEDC7D34FAC2F2FE857A28DE876528691482F6.asc
env | gpg --encrypt --always-trust -a -r stefan@sdroege.de
