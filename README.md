# IGC Menu

Twitter bot that tweets Incheon Global Campus cafeteria menu

## Usage

[IGC Menu](https://twitter.com/igcmenu)

## Deployment

Set time zone

```bash
sudo dpkg-reconfigure tzdata
```

Install packages

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install python3-pip -y
```

```bash
git clone https://github.com/yehwankim23/igc-menu.git
```

```bash
pip3 install -r requirements.txt --upgrade
```

Run

```bash
vim main.py
```

```bash
nohup python3 main.py > output.log &
```
