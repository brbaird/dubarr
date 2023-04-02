# Dubarr

Dubarr is a web app used to check if animes in Sonarr are dubbed or not.
It has views that are color-coded depending on dub status
for an entire series, seasons within that series, and episodes
within those seasons.

It is still very much a work in progress, but is in a mostly-working
state. Improvements are planned and coming!

### Installation

The best way to run Dubarr is through Docker.
You must create a config.py file and pass it to the container
at `/app/config.py`. An example config.py file can be found
[here](https://github.com/brbaird/dubarr/blob/main/example_config.py).
It is recommended to simply copy and paste that into your own config.py file,
and change only the settings that apply to you.

`docker run -p 8080:8080 -v /path/to/config.py:/app/config.py brbaird/dubarr`