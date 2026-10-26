# bend-course

A complete, self-paced [Bend](https://github.com/HigherOrderCO/Bend) curriculum in Markdown: 36 lessons across Beginner, Intermediate and Advanced, each level ending in a capstone project. It is the sibling of [rust-course](https://github.com/HunterGHall/rust-course) and follows the same shape.

Bend is a high-level, Python-looking, purely functional language that runs on the HVM2 runtime and parallelises your code automatically — on every CPU core, or on a GPU — with no threads, locks or `async`.

**Read it online:** https://hunterghall.github.io/bend-course/

The buildable source of the three capstones lives in [`capstones/`](capstones) (task tracker, expression calculator, parallel lab) and is built, tested and smoke-run by CI. CI also **runs every Bend code block in the lessons** against the real compiler, and checks the output the lesson claims (`tools/check_examples.py`).

To preview the site locally:

```bash
pip install mkdocs-material
mkdocs serve
```

To check the lesson code yourself (needs `cargo install hvm bend-lang` and a C compiler):

```bash
python3 tools/check_examples.py            # compile and run every ```bend block in docs/
python3 tools/sync_capstones.py --check    # confirm lessons show the current capstone source
bash capstones/ci.sh                       # build, run and test the three capstones
```

The course targets **Bend 0.2.38** (HVM 2.0.22) on Linux and macOS.
