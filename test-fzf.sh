#!/bin/bash

{
printf "First line\n"
sleep 1
printf "Second line, block end\0"
sleep 1
printf "third line\n"
sleep 1
printf "fourth line, block end\0"
sleep 1
printf "fifth line, no block end\n"
sleep 1
} | fzf --read0 --no-sort --reverse
