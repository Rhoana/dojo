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

### Merge Tool
The merge tool can be used to group segments of different labels to one label.
1. Activate the merge tool via icon or use keyboard shortcut 1.
2. Click on the label which you want to propagate to other labels (master).
3. Click on any other labels (slaves) to add them to the master segment.
4. To select another master label, hit ESC
5. Exit merge mode by clicking on the icon or use keyboard shortcut 1.

### Split Tool
The split tool can be used to split one label into two (or more).
1. Activate the split tool via icon or use keyboard shortcut 2.
2. Click on the label which you want to split. The region will appear without overlay.
3. Draw a line fully across the label where you want to split it. The line appears in blue.
(To cancel the split hit ESC and choose another label to split.)
4. A green split line gets calculated and appears.
Important: if no green line appears, just draw the blue line again.
5. If you are not satisified with the green line hit ESC and use the - (thinner) or = (thicker) keys to adjust the brush size. Then, draw the blue line again.
6. Once the green line looks right, click on either side of it to accept the split. The clicked region will preserve the label id from the original label.
7. Exit split mode by clicking on the icon or use keyboard shortcut 2.

### Adjust Tool
The adjust tool can be used to change the boundaries of a label in a fine-grained fashion (pixel by pixel).
1. Activate the adjust tool via icon or use keyboard shortcut 3.
2. Click on the label which you want to adjust. All other labels will be hidden.
3. It can be useful to deactivate border lines by hitting A.
4. Draw anywhere in the color of the selected label to extend it.
Use the - (thinner) or = (thicker) keys to adjust the brush size.
5. Press TAB to accept the changes or ESC to discard them.
6. Exit adjust mode by clicking on the icon or use keyboard shortcut 3.

### Collaboration Mode
The collaboration mode can be used to perform simultaneous proofreading among multiple users.
Activate the collaboration mode via icon or use keyboard shortcut 5.
As soon as other users also activate the collaboration mode, there position in the image volume gets synchronized along all collaborators.
In 2D, other users are only shown if they are working on the current slice.
It is also possible to mark a complication or a problem by hitting Z. This mark then gets propagated among all users in 2D and 3D.
In 3D, other users are always shown as needles (or pins). One can click on a pin or a exclamation mark to jump to the slice of interest.
In general, all actions (split, merge, adjust) get synchronized among all connected clients. Each action results in an entry in the log (bottom right).





### USAGE:

```
./dojo.py /PATH/TO/MOJO/FOLDER/WITH/IDS/AND/IMAGES/SUBFOLDERS
```

