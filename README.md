# MWIKI

The mini command line wiki

---

`mwiki` is a very minimal command line wiki. It depends on [Tup](https://github.com/gittup/tup), [w3m](http://w3m.sourceforge.net/), and [swish++](http://swishplusplus.sourceforge.net/). `mwiki` supports almost none of the traditional wiki features, opting instead to provide easy page linking, and a simple command line interface.

`mwiki` is setup to leverage the power of a build system to generate it's pages (in this case, Tup). This allows `mwiki` to provide a sensible default for building pages, and then ignore exactly how pages end up getting built.

By modifying the build system rules, `mwiki` can support plugins that do all sorts of things. For example, generate a meta-page that lists all of the dead links (see plugins/missing.sh).
