set -ev

cd $1
watch -n 5 cocalc cloudfs compact 