#!/bin/bash
set -ev
mysql -uroot -e "create database playero;"
mysql -uroot playero < tests/res/playero.sql
svn $SVNPARAMS --depth empty co svn://www.telenet.com.py/playero/playero Playero
svn $SVNPARAMS --set-depth infinity up Playero/base
svn $SVNPARAMS --set-depth infinity up Playero/core
svn $SVNPARAMS --set-depth infinity up Playero/standard
svn $SVNPARAMS --set-depth infinity up Playero/settings
svn $SVNPARAMS --set-depth empty    up Playero/extra
svn $SVNPARAMS --set-depth infinity up Playero/extra/StdPy
mv Playero/settings/settings.xml.example Playero/settings/settings.xml
sed -i "s/MP3_Manager/StdPy/g" Playero/settings/settings.xml
sed -i '/hansa/d' Playero/settings/settings.xml
python scripts/updateConfig.py
