# Selenobuster
Designed to enumerate websites that always return a 200 OK

## Requirements
This was developed with Python 3.8.2; any OS running this version of Python should work.

## Usage

### Launching

All options can be seen by typing 

```
Linux:
python3 selenobuster.py -h
Windows:
python selenobuster.py -h
```

Required launch arguments:

* url
* wordlist
* error_xpath_element

When a page does not exist, most websites will behave in a predictable fashion such as displaying a message saying "404 not found", even if the HTTP response is 200 OK. 
By providing the xpath associated with the error message, the program will determine if the page is valid or not.

Example:

```
python3 selenobuster.py "http://victimwebsite.com/" "./wordlist.txt" "//div/h1/" (If the xpath //div/h1 exists, it is assumed that the website is displaying an error such as "404 not found")
```

## Installation

### Python standard
* Open up a terminal and clone the repo
* Change to the repo's folder
* Type "pip install -r requirements.txt"
* Run selenobuster.py using the information in the **Usage** section

### Python virtual environment
* Open up a terminal and clone the repo
* Change to the repo's folder
* Type "pip install pipenv" (Some users may need to use "pip3" instead of "pip")
* Type "pipenv install --ignore-pipfile"
* After successful installation, type "pipenv shell" (selenobuster.py will only work inside a pipenv shell)
* Run selenobuster.py using the information in the **Usage** section