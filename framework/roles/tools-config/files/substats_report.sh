#!/bin/bash
#
# Create a daily substats.csv file with data from Marketplace, eu-gb and ay-syd
#
# delete any existing CSV files
rm *.csv
# Marketplace
python substats.py --ung=https://<ung username>:<ung password>@ibmug.mybluemix.net --output=usanstatus.csv anproddb <cloudant account password>
# eu-gb
python substats.py --ung=https://<ung username>:<ung password>@user-and-groups.eu-gb.mybluemix.net --output=euanstatus.csv anbmeugbdb <cloudant account password>
# au-syd
python substats.py --ung=https://<ung username>:<ung password>@user-and-groups.au-syd.mybluemix.net --output=auanstatus.csv anbmausyddb <cloudant account password>
# Combine CSV files into one
cat usanstatus.csv euanstatus.csv auanstatus.csv > substats.csv
# Remove region CSV files, keep combined CSV
# rm usanstatus.csv euanstatus.csv auanstatus.csv
# email CSV file
mail -s "Substats CSV" ldm@us.ibm.com,wenlinhe@cn.ibm.com -A substats.csv < /home/opsadmin/scripts/substats.csv
