DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OPENSEADRAGON=$DIR/../../../openseadragon

# switch to openseadragon clone
cd $OPENSEADRAGON
grunt --force

cp -R build/openseadragon $DIR/../lib/
