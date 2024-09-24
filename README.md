# fromregs

Analogous to [fromfilename](https://github.com/beetbox/beets/blob/master/beetsplug/fromfilename.py) but adding the option to configure regex patterns to filter results more precisely.

## Installation

Directly inject from from this repository:

```shell
pipx inject beets git+https://github.com/whatphilipcodes/fromregs
```

Then add the plugin to your config:

```yaml
[...]
plugins: fromregs [...]
[...]
```

## Configuration

The following config replicates the default settings:

```yaml
fromregs:
  custom_matchlist:
    [
      '^(?P<artist>.+)[\-_](?P<title>.+)[\-_](?P<tag>.*)$',
      '^(?P<track>\d+)[\s.\-_]+(?P<artist>.+)[\-_](?P<title>.+)[\-_](?P<tag>.*)$',
      '^(?P<artist>.+)[\-_](?P<title>.+)$',
      '^(?P<track>\d+)[\s.\-_]+(?P<artist>.+)[\-_](?P<title>.+)$',
      '^(?P<track>\d+)[\s.\-_]+(?P<title>.+)$',
      '^(?P<track>\d+)\s+(?P<title>.+)$',
      "^(?P<title>.+) by (?P<artist>.+)$",
      '^(?P<track>\d+).*$',
      "^(?P<title>.+)$",
    ]
  bad_title_matchlist: ["^$"]
  artist_post_sub: []
  title_post_sub: []
  final_trim: True
```

## Reference

`custom matchlist`<br>
Works via the capture groups `<artist>` (album or track artist), `<track>` (track number) and `<title>` (album or track title). The `<tag>` capture group is only used when importing more than one track as an album. <i>This field cannot be an emtpy list!</i>

`bad_title_matchlist`<br>
Used to determine if a track is processed (matches the list) or is skipped entirely. <i>This field cannot be an emtpy list!</i>

`artist_post_sub`<br>
Removes parts of the artist result that match with this list as a post-processing step.

`title_post_sub`<br>
Removes parts of the title result that match with this list as a post-processing step.

`final_trim`<br>
If true, removes excess white space on all results individually as the last step before applying the results.
