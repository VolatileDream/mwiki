# MWIKI

The mini command line wiki

---

`mwiki` is a very minimal command line wiki. It supports almost none of the traditional wiki features, opting instead to provide easy page linking, and a simple command line interface.

`mwiki` depends on [python3] and [sqlite]. Internally it implements a pseudo build system (like [Make] or [Tup]), and provides a standardized plugin architecture for adding new functionality.

---

## Getting Started

```shell
# Download the repo
> git clone https://github.com/VolatileDream/mwiki.git my-local-mwiki
# Ensure the mwiki executable is on your PATH
> PATH="$PATH:my-local-mwiki"
# create your projects mwiki instance
> mwiki init $project_root wiki-subdir
```

---

## Dependencies

`mwiki` depends on a few different programs, and can be extended to use even more. They are:

  * python3
  * sensible-browser - configure via BROWSER variable
  * sensible-editor - configure via EDITOR variable

Some of the plugins used my mwiki also depend on other programs. They include:

  * swish++ - search++ plugin
  * bash & other unix utilities - journal plugin

[Tup]: https://github.com/gittup/tup
[Make]: https://www.gnu.org/software/make/
[python3]: https://python.org
[sqlite]: https://sqlite.org
