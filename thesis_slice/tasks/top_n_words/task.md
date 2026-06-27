# top_n_words

Implement `top_n_words(text, n)` in `solution.py`.

Return a list of `(word, count)` tuples for the `n` most frequent words in
`text`. Rules:

- Case-insensitive: `"The"` and `"the"` are the same word; return words lowercased.
- A "word" is a maximal run of alphanumeric characters; split on everything else.
- Sort by descending count. **Break ties alphabetically (ascending).**
- If there are fewer than `n` distinct words, return all of them.
- Empty text returns `[]`.
