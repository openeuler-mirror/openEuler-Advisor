#!/bin/bash

name=$1
repo=$2
prefix=$3

cd temp/$1
git tag -l --sort -version:refname "$3*"

