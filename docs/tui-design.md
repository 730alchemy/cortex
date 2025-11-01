# Cortex TUI

## Overview
Provide a chat interface for users to interactively query for knowledge about a software project. The interface provides these tabs

| Tab     | Function                                      | Components                          |
| ------- | --------------------------------------------- | ----------------------------------- |
| Query   | chat interface for interactive query          | - Project selector<br>- chat window |
| Project | display information about the current project |                                     |
## Query Tab
Key points
- project selector
	- displays all projects available to the user. The Cortex TUI calls the Cortex API at startup time to acquire the list of projects
- chat window
	- user engages in a query-response dialog with the Cortex knowledge management system
	- each query is submitted to the Cortex API for a response. The API call includes the project id
	- each query can be collapsed and expanded. Collapsing a query collapses both the query and the response
## Project Tab
Display the following information about the project
- information sources
	- information sources are acquired by calling the Cortex API. 
	- the API response will be a list of objects
		- each object corresponds to an information source
		- each source object will include a name and a type. Examples of type include github, Notion, Linear, Google Docs. 
		- for each source object, the remaining keys will be depend on the source. For example, a github source will include a repo name and url, and a Notion source will include a workspace name and id
	- Cortex TUI will cache the information sources for the session

## Configuration File
The configuration file uses TOML

Configuration schema

```toml
[cortex-api]
url = ''
username = ''
password = ''
database = ''

[logging]
level = 'debug'
```