#!/bin/bash

name=$1
repo=$2

mkdir -p temp
cd temp
git clone $2
