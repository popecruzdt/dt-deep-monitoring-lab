### SSH
connect to instance via ssh using private key
```
ssh -i <key-name.pem> ubuntu@<hostname-or-ip-addr>
```
become root user
```
sudo su -
```
update packages
```
apt-get update
```
install docker.io
```
apt install docker.io
```
download docker-compose 1.29.2
```
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```
download example-voting-app from github
```
cd /opt
git clone https://github.com/popecruzdt/example-voting-app.git
cd example-voting-app
```
build example-voting-app
```
docker-compose build
```
launch example-voting-app
```
docker-compose up -d
```
