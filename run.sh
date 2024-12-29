#!/bin/bash


cd /home/dmitrii/PycharmProjects/LeipzigAnnouncments/ || exit
# Activate the virtual environment
source /home/dmitrii/PycharmProjects/LeipzigAnnouncments/venv/bin/activate

# Run the Python script
python /home/dmitrii/PycharmProjects/LeipzigAnnouncments/main.py

# Deactivate the virtual environment
deactivate
read -p "Press Enter to exit..."