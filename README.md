**UPDATE:** A desktop compatible version of Dojo by Hidetoshi Urakubo, Kyoto University: https://github.com/urakubo/Dojo-standalone

RhoANA: Dojo
============

Distributed Proofreading of Automatic Segmentations



## Installation & Setup
The Dojo server was tested on Mac OS X and Ubuntu Linux. It is Python-based and requires some freely available libraries. Detailed installation instructions can be found [here](https://github.com/Rhoana/dojo/wiki/Dojo-Installation).

The Dojo web-client runs on all browsers. Please view the [video](https://youtu.be/EHU7eGI5ixs) for setup instructions. Current limitations: input data must not exceed 32-bits and must be 1024x1024x1024 or less in size.

## Tutorial Videos
The following videos demonstrate Dojo's functionality.
* [Merge, Split & Adjust](https://youtu.be/WoezzrYjzY4)
* [3D Rendering](https://youtu.be/xM5jsWn_2ho)
* [Collaboration Mode](https://youtu.be/rlaBqVg8d2E)

## Usage Instructions

### Viewing and basic interaction
Mouse 2D	Keyboard
* mousewheel: zoom in/out
* right: translate

Mouse 3D
* mousewheel: zoom in/out
* left: rotate
* middle: translate

Keyboard: 
* W: Next slice
* S: Previous slice
* Q: Toggle segmentation overlay
* A: Toggle borders
* E: Increase segmentation opacity
* D: Decrease segmentation opacity
* X: Zoom in
* C: Zoom out
* L: Lock/Unlock segment

Show/Hide 3D Rendering mode or use keyboard shortcut 4 (initial loading might take a few seconds).

USAGE:

./dojo.py /PATH/TO/MOJO/FOLDER/WITH/IDS/AND/IMAGES/SUBFOLDERS

