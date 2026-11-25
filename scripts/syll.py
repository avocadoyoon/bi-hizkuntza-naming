import re
def eu_syll(w):
    s=re.sub(r'([aeo]i|[ae]u|ui)','V',w.lower().strip())
    return len(re.findall(r'V|[aeiou]',s))

# simple Basque syllable counter

# Limits:
# Other vowel pairs such as ia and ua are counted as two syllables (hiatus). Dialects may differ.
# It only knows a e i o u, so a loan word with unusual letters would be miscounted.
# ui is merged into one syllable, which is debatable. No selected item hinges on it.
