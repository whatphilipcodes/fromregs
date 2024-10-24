# fromregs

Analogous to [fromfilename](https://github.com/beetbox/beets/blob/master/beetsplug/fromfilename.py) but adding the option to configure regex patterns to filter results more precisely.

## Installation

Directly inject from this repository:

```shell
pipx inject beets git+https://github.com/whatphilipcodes/fromregs
```

Then add the plugin to your config:

```yaml
plugins: fromregs [...]
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
  artist_post_sub: ['\s{2,}']
  title_post_sub: ['\[.*?\]', '\s{2,}']
  final_strip: yes
  fill_album_from_title: no,
  limit_tracknumber: 25,
```

If you are trying to come up with your own regex patterns this plugin delivers more detailed logs when running verbose at level 2:
```bash
beet -vv import path/to/track(s)
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

`final_strip`<br>
If true, removes excess white space on all results individually as the last step before applying the results.

`fill_album_from_title`<br>
Uses the title as album, if that matches your search strategy.

`limit_tracknumber`<br>
Threshold to decide wether a number should be treated as a track or only used for album, artist and title names.
