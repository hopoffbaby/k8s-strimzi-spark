
apt install python3-venv -y
python3 -m venv megacollector_env
source megacollector_env/bin/activate
pip3 install tqdm psutil

python3 megacollector.py --processes 128 --monitor --log_errors /mnt/Race2024/ ~/race2024metadata.csv