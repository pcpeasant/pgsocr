# pgsocr
Convert Blu-Ray SUP subtitles to SRT using Tesseract.

### Tesseract Installation

See: https://tesseract-ocr.github.io/tessdoc/Installation.html \
Make sure to install all the required language packs and note down the location of the 'tessdata' directory since it must be supplied manually to pgsocr.

### Usage:

    Options:
    -i: Specify the path to the SUP file or (batch mode) directory.
    -o: Specify the path to the output directory.
    -t: Specify the path to the tessdata directory.
    -l: Specify the list of languages to use separated by commas (Uses English if unspecified)

    Examples:
    # Single file
    pgsocr -i /path/to/file -o path/to/outputdir -t /path/to/tessdata -l eng,jpn

    # Multiple files in a directory
    pgsocr -i /path/to/inputdir -o /path/to/outputdir -t /path/to/tessdata
