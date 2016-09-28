## UCR Term Dates
This is a very basic API that scrapes the UCR Academic Calendar "print preview"
page [http://registrar.ucr.edu/registrar/academic-calendar/print-academic-calendar.html]
(http://registrar.ucr.edu/registrar/academic-calendar/print-academic-calendar.html) 
for the First and Last day of instruction for a given quarter term and year.

The first and last day of instruction are returned in json format along with 
the original term and year requested.

### Using the API
The API call format is https://ucr-term-dates.appspot.com/[quarter]?year=[year]

The response will be a json result in the format
```json
{
    "end": "YYYY-MM-DD", 
    "start": "YYYY-MM-DD", 
    "term": "[quarter]", 
    "year": "[year]"
}
```

For example, a `GET` request to the URL 
https://ucr-term-dates.appspot.com/fall?year=2016 
will give a json response
```json
{
    "end": "2016-12-02", 
    "start": "2016-09-22", 
    "term": "FALL", 
    "year": "2016"
}
```

An invalid request or a request for a term no listed on the UCR Academic 
Calendar page will return `-1` for both `end` and `start`.

### Known Issues
This API will only scrape the UCR Academic Calendar print preview page. At the 
time that this was developed, Summer Sessions are NOT listed on that page and 
will therefore result in an erroneous response of `-1` for the first and last 
days of instruction.

### Feedback
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Licensing
See [LICENSE](LICENSE)

## Author
Joel Gomez
