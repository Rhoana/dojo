RhoANA: Dojo
============

Distributed Proofreading of Automatic Segmentations

Instructions: http://rhoana.org/dojo/


## USAGE:

./dojo.py ../path/to/mojo/ ../path/to/temp/ [<<Port Number>>]


## Notes 2016-06-08

TODO: 

- Fix interesting bug where blue split line continues even after split made
- Add save warning when approaching new_merge_table limit
- Add percentage feedback while saving
- **Add multi-layer depth cutting**

## Merge table objects

- Client
	- \_temp\_merge\_table
		- teporary usage to draw, redo, and undo merges
		- sent to Server in send\_temp\_merge\_table()
	- \_new\_merge\_table
		- all merges currently sent to the shader
		- received from Serverside send\_new\_merge\_table()
- Server
	- \_\_new\_merge\_table
		- accumulates \_temp\_merge\_table of all Clients
		- sent to update all Clientside \_new\_merge\_table
	- \_\_hard\_merge\_table
		- updated from database.\_merge\_table on save()
	- database.\_merge\_table
		- accumulates \_\_new\_merge\_table on save()