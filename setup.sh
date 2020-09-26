echo -e "\nUpgrading pip"
python -m pip install --upgrade pip

echo -e "\nInstall virtual-environment"
pip install --upgrade virtualenv

echo -e "\nCreating a virutal environment"
virtualenv ./.venv

# Activating the virtual environment.
source .venv/bin/activate

echo -e "\nInstalling the required packages"
pip install -r ./requirements.txt

echo -e "
    Setup executed successfully.

    Activate the virtual-environment using 
        \`source .venv/bin/activate\`
    
    Once done, follow the rest of instructions in the setup.
"
