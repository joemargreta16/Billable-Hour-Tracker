#!/bin/bash
# This script removes the integrity attribute from the Chart.js script tag in templates/base.html

sed -i.bak '/chart\.umd\.min\.js/ s/integrity="[^"]*" //' templates/base.html
