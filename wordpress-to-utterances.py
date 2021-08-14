# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <http://unlicense.org/>

import os
import sys
import time

from xml.dom.minidom import parse
from collections import defaultdict

from github import Github

fn = sys.argv[1]
dom = parse(fn)

class settings:
    """
    Class for easy access to env vars
    """
    def __init__(self, di):
        self.di = di
        
    def __getattr__(self, k):
        return self.di[k]
        
settings = settings(os.environ)

# assert the right environment variable are set
settings.TOKEN, settings.REPO, settings.SITE_NAME, settings.URL

g = Github(settings.TOKEN)
repo = g.get_repo(settings.REPO)
issues = list(repo.get_issues())

def issues_by_post(title, url):
    """
    Returns or creates issue by post title    
    """
    
    name = " | ".join((title, settings.SITE_NAME))

    filtered = [i for i in issues if i.title == name]
    if filtered:
        return filtered[0]        
    
    issue = repo.create_issue(title=name, body=f"#{name}\n\n\n\n[url](url)")
    time.sleep(5)
    issues.append(issue)
    return issue


class xml_wrapper:
    """
    Class to allow easy access to XML nodes
    """
    
    def __init__(self, node):
        self.node = node
        
    def __getattr__(self, k):
        try:
            return self.node.getElementsByTagName("wp:" + k)[0].firstChild.nodeValue
        except:
            return self.node.getElementsByTagName(k)[0].firstChild.nodeValue
        
    def _get_parent(self):
        return xml_wrapper(self.node.parentNode)
        
    parent = property(_get_parent)
    
posts = defaultdict(list)
comment_bodies = {}

# Find comments and sort by id (chronologically?)
for cmnt in sorted(map(xml_wrapper, dom.getElementsByTagName('wp:comment')), key=lambda c: int(c.comment_id)):
    
    # Only emit approved comments
    if cmnt.comment_approved != "1": continue
    
    # Lookup or create github issue
    issue = issues_by_post(cmnt.parent.title, url="/".join((settings.URL, "posts", cmnt.parent.title.lower().replace(" ", "-"))))
    
    # Build comment body
    body = ""    
    if int(cmnt.comment_parent):
        # Cite parents inline in the post body
        body += "\n".join(("> " + x for x in comment_bodies[cmnt.comment_parent].split("\n")))
        body += "\n\n"
        
    # Do some string replacements for paragraph and code blocks
    content = cmnt.comment_content.replace("\n", "\n\n").replace("<code>", "```").replace("</code>", "```")
    
    # Append comment author and date
    body += f"Original comment by **{cmnt.comment_author}** on **{cmnt.comment_date}**\n\n---\n\n{content}"
    
    # Store comment body in case it is cited later by another comment
    comment_bodies[cmnt.comment_id] = body
    
    # Post to github
    issue.create_comment(body=body)
    
    # Rate limiting
    time.sleep(5)
