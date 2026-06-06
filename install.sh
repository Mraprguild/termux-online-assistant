#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "Installing Mraprguild Online Assistant..."
pkg update -y
pkg install python termux-api -y
python -m pip install --upgrade pip
pip install -r requirements.txt

chmod +x assistant.py start.sh
mkdir -p "$HOME/.mraprguild-assistant"
cp assistant.py requirements.txt start.sh "$HOME/.mraprguild-assistant/"

if ! grep -q "alias mra-assistant=" "$HOME/.bashrc" 2>/dev/null; then
  echo "alias mra-assistant='cd \$HOME/.mraprguild-assistant && python assistant.py'" >> "$HOME/.bashrc"
fi

echo
echo "Installation complete."
echo "Run now: ./start.sh"
echo "Later run: mra-assistant"
