## chem-scrape

### Using chem-scrape
Using chem-scrape is easy.

1. Create a file containing a compound group ID and a compound (see 
[example.txt](example.txt))
  * You include multiple compounds on separate lines, but be warned, 
  **chem-scrape is SLOW!!!**
2. Run chem-scrape: `./scrape [your file]`
3. chem-scrape will output a `output.json` file with your results
  * If there were any errors, chem-scrape will generate a corresponding log file 
with which items failed so that you can debug, or retry them at a later date 
when chem-scrape is updated (unlikely).

### Known Issues
chem-scrape can't get the group id of a compound on it's own due to the data 
that's being parsed not containing a trace of it.

Make sure your file is formatted just like [example.txt](example.txt)! Whatever 
bugs were discovered during development have been uh... "patched?", but surely 
more are lurking in there in the deep.

### Feedback
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Licensing
See [LICENSE](LICENSE)

## Author
Joel Gomez
