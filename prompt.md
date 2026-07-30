# Lenrose
## Scientific Metadata Search Engine

### Application
Create one python application which will start out with no data, showing an Terminal User Interface (TUI), which will allow the user to ingest data from a connected Tiled server. The TUI will prompt users interactively to connect to Tiled by providing a URL, username/password or API key according to the Tiled documentation (https://blueskyproject.io/tiled/user-guide/authentication.html).
Once a connection is made, enumerate a list of containers that are available to the user with checkmarks next to them so they may be selected, and also provide an ability to limit the number of results for each container.

With this selection, download only the metadata for each record that the user has access to and enumerate a list of all potential keys, identifying their values datatypes, including nested keys.

With that metadata retained in memory or written to a temporary disk location, build a typesense collection with a schema based off of the selected keys. While selecting keys in the TUI, ask for potential options like if the key should be a facet e.g.

After we index all the records (or if an index already exists, feel free to utilize a small db like sqlite to track state of this application), start a web application that will serve a search interface using a typesense client that can perform indexing, show all available facets, present a list of records returned by search and be able to load the metadata from tiled via the container/UUID which will get stored in the index. Store container information in typesense in a way that it can be used as a facet later.

Set up a method using webhooks to subscribe to the selected Tiled containers to ingest new records as they are generated. Enable the web interface or TUI to rebuild the typesense collection as needed. Also allow expanding the selected keys and rebuilding the collection schema.

Allow for an interface to edit the frontend to be recomposible, i.e. be able to move or remove the searchbar, add or change default facets etc.
One customization option to be added would enable actually loading the data from the paginated search results in the way that displays it graphically, following the data viewers used in Tiled's web frontend example here (https://github.com/bluesky/tiled/tree/main/web-frontend). Store whatever information would be needed to determine if a record's data can be displayed in the typesense instance.
This would be for displaying images, dataframes e.g.