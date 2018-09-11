#!/usr/bin/env python

# Author: Steven Miller

# TODO: move code out of init file

import requests
import urllib
import sys
import os
import lxml.html as html
from random import randint
from subprocess import check_output
import pydoc


def build_search_url(query):
    """
    Build Google URL with 'I'm Feeling Lucky'
    Limit results to docs.aws.amazon.com
    Prepend 'aws cloudformation' to the search
    Append the argument as the search query
    """
    google_url = []
    # Build URL to query Google
    google_url.append('https://www.google.com/search?')
    # I'm feeling lucky: go to first result
    google_url.append('btnI=1')
    # Limit results to only this specific website
    google_url.append('&as_sitesearch=docs.aws.amazon.com')
    # Build query
    query = "aws cloudformation " + query
    # This line escapes spaces and the like
    query = urllib.quote_plus(query.strip())
    # Attach query to URL
    google_url.append("&q=")
    google_url.append(query)
    return "".join(google_url)


def get_docs_html_content(url):
    """
    Given an aws cloudformation docs URL,
    get the webpage and parse the HTML
    extracting the relevant HTML for making
    a man-page-like document
    """
    # Relevant tags
    want_tags = ['p', 'h1', 'h2', 'h3', 'div']
    # Relevant classes and ids for div elements
    want_divs = ['variablelist', 'aws-note', 'YAML']
    # Get request to amazon
    response = requests.get(url)
    # Parse the raw HTML
    parsed = html.fromstring(response.text)
    # Print out the HTML elements we want
    try:
        main_content = parsed.get_element_by_id("main-col-body")
    except KeyError:
        print("Sorry! Did not find a document.")
        print(url)
        exit(1)
    content = []
    for el in main_content:
        if (el.tag not in want_tags) or \
           (el.tag == 'div') and not ( \
             ('class' in el.attrib.keys() and el.attrib['class'] in want_divs) or \
             ('id' in el.attrib.keys() and el.attrib['id'] in want_divs)
           ):
            continue
        content.append(html.tostring(el))
    return "".join(content)


def format_html_content(content):
    """
    Given HTML content as a string
    pass the HTML through the terminal
    program 'links' to format into
    a document
    """
    # Use a random file name to avoid collision
    # for writing temporary file
    temp_file = str(randint(0, 10000000000)) + "-tmp-cfn-man.html"
    try:
        with open(temp_file, 'w') as f:
            f.write(content)
        return check_output(['links', '-dump', temp_file])
    except OSError as e:
        if 'No such file or directory' in str(e):
            print(
                "Please make sure the command line utility 'links' is installed"
            )
            exit(1)
        raise e
    # Use finally to ensure resource is cleaned up
    finally:
        os.remove(temp_file)


def main():
    if len(sys.argv) < 2:
        print("usage:\ncfn_docs security group\ncfn_docs ec2")
        exit(1)
    query = []
    for arg in sys.argv[1:]:
        query.append(arg)
        query.append(" ")
    url = build_search_url("".join(query))
    html_content = get_docs_html_content(url)
    doc = format_html_content(html_content)
    # this is the equivalent of piping into 'less'
    pydoc.pager(doc)
