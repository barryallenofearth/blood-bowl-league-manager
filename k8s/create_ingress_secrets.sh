#!/bin/bash
openssl req -x509 -new -nodes -key ca.key -sha256 -subj "/CN=kubernetes-master.fritz.box" -days 3650 -out ca.crt -extensions san -config <(
echo '[req]';
echo 'distinguished_name=req';
echo '[san]';
echo 'subjectAltName=DNS:thinkcentre-m929.fritz.box')


microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n kube-system
microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n baby-dimensions
microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n price-tracker
microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n blood-bowl-league-manager
microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n radio-station-scraping
microk8s kubectl create secret generic ingress-cert --from-file=ca.crt=ca.crt --from-file=ca.key=ca.key -n paypal-donation-mail-scraper
