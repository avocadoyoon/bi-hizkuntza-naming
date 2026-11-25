# Selection notes
**Source:** MULTIMAP norms (git.bcbl.eu/sgisbert/multimap2). Pictures: DATA/Stimuli/New_Objects, New_Verbs.
80 items = 20 nouns + 20 verbs x Spanish + Basque; the two languages share no picture.

**Rules:** name agreement >=80 in the language's own norms; non-cognate = normalised Levenshtein(ES,EU) >=.6 (own threshold);
one-word names; each word used once per language. A handful of spreadsheet rows that looked dubious were excluded by hand.

**Selection:** random-restart swap search maximising the smallest Welch-test p across 8 comparisons (log frequency and syllables x
ES-vs-EU nouns, ES-vs-EU verbs, ES noun-vs-verb, EU noun-vs-verb). Final smallest p = .124.

Basque nouns are counted WITH the article (word, LOG10_FREQ_a, NUM_SYLL), as in the sheet; the cognate check uses the bare form.
