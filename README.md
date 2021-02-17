# MWIKI

The mini command line wiki

---

`mwiki` is a very minimal command line wiki. It supports almost none of the traditional wiki features, opting instead to provide easy page linking, and a simple command line interface.

`mwiki` depends on [Tup], and is setup to leverage the power of the build system (Tup) to generate it's pages. This allows `mwiki` to provide a sensible default for building pages, and then ignore exactly how pages end up getting built.

By modifying the build system rules, `mwiki` can support plugins that do all sorts of things. For example, generate a meta-page that lists all of the dead links (see plugins/missing/run).

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

  * sensible-browser - configure via BROWSER variable
  * sensible-editor - configure via EDITOR variable
  * [Tup]

Some of the plugins used my mwiki also depend on other programs. They include:

  * swish++ - search++ plugin
  * python3 - tapestry plugin

Not mentioned in either list is the large set of standard unix utils, such as awk, sed, find, etc.

[Tup]: https://github.com/gittup/tup
