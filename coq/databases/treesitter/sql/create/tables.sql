BEGIN;


CREATE TABLE IF NOT EXISTS buffers (
  rowid    INTEGER NOT NULL PRIMARY KEY,
  filetype TEXT    NOT NULL
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS buffers_filetype ON buffers (filetype);


CREATE TABLE IF NOT EXISTS words (
  buffer_id INTEGER NOT NULL REFERENCES buffers (rowid) ON UPDATE CASCADE ON DELETE CASCADE,
  word      TEXT    NOT NULL,
  lword     TEXT    NOT NULL,
  kind      TEXT    NOT NULL,
  pword     TEXT,
  pkind     TEXT,
  gpword    TEXT,
  gpkind    TEXT,
  UNIQUE (buffer_id, word)
);
CREATE INDEX IF NOT EXISTS words_word ON  words (word);
CREATE INDEX IF NOT EXISTS words_lword ON words (lword);


CREATE VIEW IF NOT EXISTS words_view AS
SELECT
  buffers.rowid AS buf_id,
  words.word,
  words.lword,
  words.kind,
  words.pword,
  words.pkind,
  words.gpword,
  words.gpkind
FROM words
JOIN buffers 
ON
  buffers.rowid = words.buffer_id;


END;
