# Repulse Analytics

This is a prototype of a CI workflow that visualizes the long term GitHub traffic data for the [qp](https://github.com/Zweih/qp) repo.

The CI workflow runs as a cronjob daily near (but not at) midnight UTC.

The Go program fetches and organizes the day's traffic data from the GitHub API (we can only get the current total downloads) into a SQLite database.

The SQLite database is stored as a GH Action artifact, so we always have access to all the DBs from the previous 90 days. The SQLite databases are microscopic in storage footprint, so this **should** never be an issue to store as an artifact.

The Python portion then pulls the data from the SQLite DB and plots the data.

Badge SVGs are generated using the latest total data.

The CI then commits those graph SVGs to an orphan branch (the branch is squashed daily so the repo does not become bloated).

That triggers the CI for rebuilding the GitHub pages URL.

Using GitHub pages results in faster load tiems as it leverages GitHub's CDN rather than loading directly from a repo. This is effective for linking to these graphs from other repos.

## GitHub Traffic Badges

![downloads-badge](https://zweih.github.io/repulse-analytics/downloads_badge.svg) 

![clones-badge](https://zweih.github.io/repulse-analytics/clones_badge.svg)

## GitHub Traffic Graphs

![Total Clones](https://zweih.github.io/repulse-analytics/total_downloads.svg)

![Total Downloads](https://zweih.github.io/repulse-analytics/total_clones.svg)
