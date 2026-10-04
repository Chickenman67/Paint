#!/bin/sh
# emit one line per _cards.py that lands, plus a final summary when all 9 exist
prev=""
for i in $(seq 1 200); do
  n=$(ls */_cards.py 2>/dev/null | grep -v psrb1257 | wc -l)
  if [ "$n" != "$prev" ]; then
    echo "cards modules landed: $n/9  [$(ls */_cards.py 2>/dev/null | grep -v psrb1257 | xargs -n1 dirname 2>/dev/null | tr '\n' ' ')]"
    prev="$n"
  fi
  if [ "$n" -ge 9 ]; then echo "ALL 9 card modules present"; break; fi
  sleep 20
done
