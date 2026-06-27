# text_justify

Implement `justify(words, max_width)` in `solution.py`.

Given a list of words and a column width `max_width`, format the text so each
line is **exactly** `max_width` characters using full justification:

- Greedily pack as many words as fit on a line (words are separated by at least
  one space). A word never exceeds `max_width`.
- For every line *except the last*, distribute spaces between words as evenly as
  possible. If the spaces don't divide evenly, the **left** gaps get one more
  space than the right gaps.
- A line containing a single word is left-justified and padded with trailing
  spaces.
- The **last line** is left-justified: single space between words, padded with
  trailing spaces on the right.

Return the list of justified lines.
