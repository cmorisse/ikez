#!/usr/bin/env bash
# Cette ligne nous permet de monter l’ « installeur » sur la machine hôte
# L'installeur est le fichier "Installer OSX Yosemite" téléchargé sur l' Appstore 
# Il faut le copier juste après le téléchargement 
hdiutil attach ~/Desktop/Install\ OS\ X\ Yosemite.app/Contents/SharedSupport/InstallESD.dmg -noverify -nobrowse -mountpoint /Volumes/install_app

#Convertir l'image de démarrage du système en format sparse
hdiutil convert /Volumes/install_app/BaseSystem.dmg -format UDSP -o /tmp/Yosemite

#Elargir l’image afin de pouvoir copier les paquets restants avec le système
hdiutil resize -size 8g /tmp/Yosemite.sparseimage

#Avec cette ligne, nous allons monter l’image en cours de création sur notre ordinateur
hdiutil attach /tmp/Yosemite.sparseimage -noverify -nobrowse -mountpoint /Volumes/install_build

#Effacer le lien symbolique vers les paquets
rm /Volumes/install_build/System/Installation/Packages

#Copier les en dur dans l'image
cp -rp /Volumes/install_app/Packages /Volumes/install_build/System/Installation/

#Copier les fichiers indispensables au bon déroulement de l’installation,
cp -rvf /Volumes/install_app/BaseSystem.dmg /Volumes/install_build/
cp -rvf /Volumes/install_app/BaseSystem.chunklist /Volumes/install_build/

#Ejecter les deux montages (install_app=source, install_build=destination)
hdiutil detach /Volumes/install_app
hdiutil detach /Volumes/install_build

#Redimensionner l’image pour qu’elle occupe uniquement l’espace nécessaire
hdiutil convert /tmp/Yosemite.sparseimage -format UDTO -o /tmp/Yosemite

#Transformer en format CDR
rm /tmp/Yosemite.sparseimage

#Conversion du format CDR vers ISO et copie sur le bureau
mv /tmp/Yosemite.cdr ~/Desktop/MACOSX-YOSEMITE.ISO